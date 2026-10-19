import io
import tempfile
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from PIL import Image
from rest_framework.test import APITestCase

from apps.comun import pruebas
from apps.convocatorias.models import Convocatoria
from apps.cuentas.models import Rol
from apps.notificaciones.models import Notificacion

from .models import Publicacion

URL = "/api/v1/muro/publicaciones/"


def imagen_png(nombre="foto.png"):
    contenido = io.BytesIO()
    Image.new("RGB", (8, 8), "navy").save(contenido, format="PNG")
    return SimpleUploadedFile(nombre, contenido.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pbconecta-pruebas-"))
class MuroTests(APITestCase):
    def setUp(self):
        self.datos = pruebas.catalogos()
        self.oficina = pruebas.usuario(Rol.OFICINA)
        self.empresa, self.reclutador = pruebas.empresa()
        self.estudiante = pruebas.estudiante()  # Programa: Software
        self.client.force_authenticate(self.oficina)

    def publicar(self, **datos):
        return self.client.post(URL, {"tipo": "NOTICIA", "titulo": "Hola", "texto": "Contenido", **datos})

    def ids(self, **parametros):
        return [p["id"] for p in self.client.get(URL, parametros).data["results"]]

    # ---------------------------------------------------------------- quién publica qué (RF-102)
    def test_tipos_por_rol(self):
        self.assertEqual(self.publicar(tipo="COMUNICADO").status_code, 201)
        self.client.force_authenticate(self.reclutador)
        self.assertEqual(self.publicar(tipo="NOTICIA").status_code, 201)
        self.assertEqual(self.publicar(tipo="OFERTA_EXTERNA", enlace_url="https://x.example").status_code, 400)
        self.client.force_authenticate(self.estudiante.usuario)
        self.assertEqual(self.publicar().status_code, 403)

    def test_empresa_sin_convenio_no_publica(self):  # RN-02
        _, reclutador = pruebas.empresa(estado="CONVENIO_VENCIDO", convenio_vigente=False)
        self.client.force_authenticate(reclutador)
        self.assertEqual(self.publicar().status_code, 403)

    def test_nadie_publica_tipo_convocatoria_a_mano(self):  # RF-35
        self.assertEqual(self.publicar(tipo="CONVOCATORIA").status_code, 400)

    def test_requisitos_por_tipo(self):  # RF-101, RF-104
        self.assertEqual(self.publicar(tipo="OFERTA_EXTERNA").status_code, 400)
        self.assertEqual(self.publicar(tipo="OFERTA_EXTERNA", enlace_url="https://bolsa.example/1").status_code, 201)
        self.assertEqual(self.publicar(tipo="EVENTO").status_code, 400)
        cuando = (timezone.now() + timedelta(days=5)).isoformat()
        self.assertEqual(self.publicar(tipo="EVENTO", fecha_evento=cuando, lugar_evento="Coliseo").status_code, 201)

    def test_imagen_valida(self):
        self.assertEqual(self.publicar(imagen=SimpleUploadedFile("x.png", b"no es imagen", content_type="image/png")).status_code, 400)
        respuesta = self.publicar(imagen=imagen_png())
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        self.assertTrue(respuesta.data["imagen"].startswith("/media/publico/muro/"))

    # ---------------------------------------------------------------- visibilidad
    def test_dirigida_a_programas_y_aviso(self):  # RF-100, RF-103, M9
        otro = pruebas.estudiante(programa=self.datos["diseno"])
        with self.captureOnCommitCallbacks(execute=True):
            dirigida = self.publicar(para_todos_programas="false", programas=[self.datos["software"].pk]).data["id"]
        general = self.publicar().data["id"]
        self.assertTrue(Notificacion.objects.filter(usuario=self.estudiante.usuario, tipo="MURO_PROGRAMA").exists())
        self.assertFalse(Notificacion.objects.filter(usuario=otro.usuario, tipo="MURO_PROGRAMA").exists())

        self.client.force_authenticate(self.estudiante.usuario)
        self.assertEqual(set(self.ids(para_mi="1")), {dirigida, general})
        self.client.force_authenticate(otro.usuario)
        self.assertEqual(self.ids(para_mi="1"), [general])
        self.assertEqual(set(self.ids()), {dirigida, general})  # «Todo el muro»

    def test_dirigida_sin_programas_es_invalida(self):
        self.assertEqual(self.publicar(para_todos_programas="false").status_code, 400)

    def test_convocatoria_en_revision_no_se_ve(self):
        convocatoria = pruebas.convocatoria(self.empresa, [self.datos["software"]])
        self.client.force_authenticate(self.estudiante.usuario)
        self.assertEqual(len(self.ids(tipo="CONVOCATORIA")), 1)
        Convocatoria.objects.filter(pk=convocatoria.pk).update(estado="EN_REVISION")
        self.assertEqual(self.ids(tipo="CONVOCATORIA"), [])

    # ---------------------------------------------------------------- moderación (RF-105)
    def test_ocultar_exige_motivo_y_solo_la_oficina_ve_lo_oculto(self):
        self.client.force_authenticate(self.reclutador)
        pid = self.publicar().data["id"]
        self.client.force_authenticate(self.oficina)
        self.assertEqual(self.client.post(f"{URL}{pid}/ocultar/", {"motivo": ""}).status_code, 400)
        with self.captureOnCommitCallbacks(execute=True):
            oculta = self.client.post(f"{URL}{pid}/ocultar/", {"motivo": "Publicidad no relacionada"}).data
        self.assertEqual(oculta["estado"], "OCULTA")
        self.assertTrue(Notificacion.objects.filter(usuario=self.reclutador, tipo="MURO_OCULTA").exists())
        self.assertIn(pid, self.ids())

        self.client.force_authenticate(self.estudiante.usuario)
        self.assertNotIn(pid, self.ids())
        self.assertEqual(self.client.post(f"{URL}{pid}/ocultar/", {"motivo": "x"}).status_code, 403)

        self.client.force_authenticate(self.oficina)
        self.client.post(f"{URL}{pid}/mostrar/")
        self.client.force_authenticate(self.estudiante.usuario)
        self.assertIn(pid, self.ids())

    def test_editar_y_eliminar_solo_el_autor_o_la_oficina(self):
        self.client.force_authenticate(self.reclutador)
        pid = self.publicar().data["id"]
        _, otro = pruebas.empresa()
        self.client.force_authenticate(otro)
        self.assertEqual(self.client.patch(f"{URL}{pid}/", {"titulo": "X"}).status_code, 400)
        self.client.force_authenticate(self.reclutador)
        self.assertEqual(self.client.patch(f"{URL}{pid}/", {"titulo": "Nuevo título"}).data["titulo"], "Nuevo título")
        self.assertEqual(self.client.delete(f"{URL}{pid}/").status_code, 204)
        self.assertEqual(Publicacion.objects.get(pk=pid).estado, "ELIMINADA")  # Borrado lógico
        self.assertNotIn(pid, self.ids())

    # ---------------------------------------------------------------- participación (RF-106, RF-107)
    def test_reaccionar_guardar_y_comentar(self):
        pid = self.publicar().data["id"]
        self.client.force_authenticate(self.estudiante.usuario)
        datos = self.client.post(f"{URL}{pid}/reaccionar/").data
        self.assertEqual((datos["me_interesa"], datos["reacciones_total"]), (True, 1))
        datos = self.client.post(f"{URL}{pid}/reaccionar/").data
        self.assertEqual((datos["me_interesa"], datos["reacciones_total"]), (False, 0))

        self.assertTrue(self.client.post(f"{URL}{pid}/guardar/").data["guardada"])
        self.assertEqual(self.ids(guardadas="1"), [pid])

        comentarios = self.client.post(f"{URL}{pid}/comentarios/", {"texto": "¿Hay cupos para tecnólogos?"}).data
        self.assertEqual(len(comentarios), 1)
        self.client.force_authenticate(self.oficina)
        self.client.post(f"{URL}{pid}/comentarios/{comentarios[0]['id']}/ocultar/")
        self.client.force_authenticate(self.estudiante.usuario)
        self.assertEqual(self.client.get(f"{URL}{pid}/comentarios/").data, [])
        self.assertEqual(self.client.get(f"{URL}{pid}/").data["comentarios_total"], 0)
