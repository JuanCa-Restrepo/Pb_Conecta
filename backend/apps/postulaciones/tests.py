import tempfile
from datetime import timedelta

from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.comun import pruebas
from apps.convocatorias import afinidad
from apps.cuentas.models import Rol
from apps.notificaciones.models import Notificacion

from .models import Postulacion

URL = "/api/v1/postulaciones/"


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pbconecta-pruebas-"))
class PostulacionTests(APITestCase):
    def setUp(self):
        self.datos = pruebas.catalogos()
        self.oficina = pruebas.usuario(Rol.OFICINA)
        self.empresa, self.reclutador = pruebas.empresa()
        self.convocatoria = pruebas.convocatoria(self.empresa, [self.datos["software"]], habilidades=["Python", "Django"])
        self.perfil = pruebas.estudiante_listo()
        self.client.force_authenticate(self.perfil.usuario)

    def postular(self, convocatoria=None):
        return self.client.post(URL, {"convocatoria": (convocatoria or self.convocatoria).pk, "mensaje_presentacion": "Hola"}, format="json")

    def como(self, usuario):
        self.client.force_authenticate(usuario)

    def cambiar(self, postulacion_id, estado, **extra):
        return self.client.post(f"{URL}{postulacion_id}/cambiar-estado/", {"estado": estado, **extra}, format="json")

    # ---------------------------------------------------------------- requisitos para postularse
    def test_postulacion_exitosa_copia_hv_y_notifica(self):  # RF-50, escenario 3
        with self.captureOnCommitCallbacks(execute=True):
            respuesta = self.postular()
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        postulacion = Postulacion.objects.get(pk=respuesta.data["id"])
        self.assertEqual(postulacion.afinidad, 50 + 18)  # Programa + 1 de 2 habilidades (35/2 ≈ 18)
        self.assertNotEqual(postulacion.hoja_vida.name, self.perfil.hoja_vida.name)  # Es una copia
        self.assertEqual(respuesta.data["historial"][0]["estado_nuevo"], "POSTULADO")
        self.assertTrue(Notificacion.objects.filter(usuario=self.reclutador, tipo="POSTULACION_NUEVA").exists())

    def test_no_habilitado_no_se_postula(self):  # RN-04
        self.como(pruebas.estudiante_listo(estado="NO_HABILITADO").usuario)
        respuesta = self.postular()
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("habilitado", str(respuesta.data["detail"]))

    def test_perfil_incompleto_no_se_postula(self):  # RN-04
        self.perfil.hoja_vida.delete(save=True)
        respuesta = self.postular()
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("hoja de vida", str(respuesta.data["detail"]))

    def test_solo_convocatorias_de_su_programa(self):  # RN-05
        diseno = pruebas.convocatoria(self.empresa, [self.datos["diseno"]])
        respuesta = self.postular(diseno)
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("programa", str(respuesta.data["detail"]))

    def test_no_se_postula_dos_veces(self):  # RN-06
        self.postular()
        self.assertEqual(self.postular().status_code, 400)

    def test_sin_limite_de_postulaciones(self):  # RN-06 (D3)
        for _ in range(7):
            otra = pruebas.convocatoria(self.empresa, [self.datos["software"]])
            self.assertEqual(self.postular(otra).status_code, 201)

    def test_otros_roles_no_se_postulan(self):
        self.como(self.reclutador)
        self.assertEqual(self.postular().status_code, 403)

    # ---------------------------------------------------------------- flujo de estados
    def test_flujo_hasta_seleccion(self):  # Escenario 4
        pid = self.postular().data["id"]
        self.como(self.reclutador)
        self.assertEqual(self.cambiar(pid, "PRESELECCIONADO").status_code, 400)  # No se salta EN_REVISION (RN-13)
        self.assertEqual(self.cambiar(pid, "EN_REVISION").data["estado"], "EN_REVISION")
        self.assertEqual(self.cambiar(pid, "PRESELECCIONADO").data["estado"], "PRESELECCIONADO")
        self.assertEqual(self.cambiar(pid, "ENTREVISTA").status_code, 400)  # Solo programando la entrevista

        cuando = (timezone.now() + timedelta(days=3)).isoformat()
        with self.captureOnCommitCallbacks(execute=True):
            respuesta = self.client.post(f"{URL}{pid}/entrevistas/", {
                "fecha_hora": cuando, "modalidad": "VIRTUAL", "lugar_o_enlace": "https://meet.example/abc",
            }, format="json")
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        self.assertEqual(respuesta.data["estado"], "ENTREVISTA")
        self.assertTrue(Notificacion.objects.filter(usuario=self.perfil.usuario, tipo="ENTREVISTA").exists())

        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(self.cambiar(pid, "SELECCIONADO").data["estado"], "SELECCIONADO")
        self.assertTrue(Notificacion.objects.filter(usuario=self.oficina, tipo="POSTULANTE_SELECCIONADO").exists())
        self.assertEqual(len(self.client.get(f"{URL}{pid}/").data["historial"]), 5)  # RF-56

    def test_no_seleccionado_exige_motivo_y_el_estudiante_lo_ve(self):  # RN-11, RF-54
        pid = self.postular().data["id"]
        self.como(self.reclutador)
        self.assertEqual(self.cambiar(pid, "NO_SELECCIONADO").status_code, 400)
        self.cambiar(pid, "NO_SELECCIONADO", motivo="Buscamos experiencia en Django")
        self.como(self.perfil.usuario)
        self.assertEqual(self.client.get(f"{URL}{pid}/").data["motivo_no_seleccion"], "Buscamos experiencia en Django")

    def test_estudiante_no_cambia_estado_pero_puede_retirarse(self):  # RF-52
        pid = self.postular().data["id"]
        self.assertEqual(self.cambiar(pid, "EN_REVISION").status_code, 400)
        self.assertEqual(self.client.post(f"{URL}{pid}/retirar/").data["estado"], "RETIRADO")
        self.assertEqual(self.client.post(f"{URL}{pid}/retirar/").status_code, 400)

    # ---------------------------------------------------------------- visibilidad y seguimiento
    def test_empresa_ajena_no_ve_la_postulacion_ni_la_hv(self):  # RN-10, escenario 7
        pid = self.postular().data["id"]
        _, ajeno = pruebas.empresa()
        self.como(ajeno)
        self.assertEqual(self.client.get(f"{URL}{pid}/").status_code, 404)
        self.assertEqual(self.client.get(f"{URL}{pid}/hoja-vida/").status_code, 404)
        self.como(self.reclutador)
        self.assertEqual(self.client.get(f"{URL}{pid}/hoja-vida/").status_code, 200)

    def test_empresa_ve_perfil_profesional_sin_documento(self):  # RF-16
        self.perfil.documento = "1000123456"
        self.perfil.save()
        pid = self.postular().data["id"]
        self.como(self.reclutador)
        perfil = self.client.get(f"{URL}{pid}/").data["perfil_estudiante"]
        self.assertEqual(perfil["telefono"], "3000000000")
        self.assertNotIn("documento", perfil)

    def test_contacto_de_empresa_visible_desde_preseleccion(self):  # RF-58
        pid = self.postular().data["id"]
        self.assertIsNone(self.client.get(f"{URL}{pid}/").data["contacto_empresa"])
        self.como(self.reclutador)
        self.cambiar(pid, "EN_REVISION")
        self.cambiar(pid, "PRESELECCIONADO")
        self.como(self.perfil.usuario)
        self.assertEqual(self.client.get(f"{URL}{pid}/").data["contacto_empresa"]["email"], self.empresa.contacto_email)

    def test_bitacora_y_notas_internas(self):  # RF-57, RF-59
        pid = self.postular().data["id"]
        self.como(self.reclutador)
        incompleto = self.client.post(f"{URL}{pid}/seguimiento/", {"tipo": "CONTACTO_EXTERNO", "texto": "Llamada"}, format="json")
        self.assertEqual(incompleto.status_code, 400)
        llamada = self.client.post(f"{URL}{pid}/seguimiento/", {
            "tipo": "CONTACTO_EXTERNO", "canal": "LLAMADA", "fecha_contacto": timezone.now().isoformat(), "texto": "Se acordó entrevista",
        }, format="json")
        self.assertEqual(llamada.status_code, 201, llamada.data)
        self.assertEqual(self.client.post(f"{URL}{pid}/seguimiento/", {"tipo": "NOTA_INTERNA", "texto": "x"}, format="json").status_code, 400)

        self.como(self.oficina)
        self.assertEqual(self.client.post(f"{URL}{pid}/seguimiento/", {"tipo": "NOTA_INTERNA", "texto": "Revisar créditos"}, format="json").status_code, 201)
        self.assertEqual(len(self.client.get(f"{URL}{pid}/").data["seguimiento"]), 2)
        self.como(self.perfil.usuario)
        self.assertEqual([e["tipo"] for e in self.client.get(f"{URL}{pid}/").data["seguimiento"]], ["CONTACTO_EXTERNO"])


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pbconecta-pruebas-"))
class ConvocatoriasEstudianteTests(APITestCase):
    """M5: lo que ve el estudiante en las convocatorias."""

    def setUp(self):
        self.datos = pruebas.catalogos()
        self.empresa, _ = pruebas.empresa()
        self.software = pruebas.convocatoria(self.empresa, [self.datos["software"]], habilidades=["Python"], titulo="Desarrollador backend")
        self.diseno = pruebas.convocatoria(
            self.empresa, [self.datos["diseno"]], titulo="Diseñador de marca", descripcion="Identidad visual", funciones="Ilustrar"
        )
        self.perfil = pruebas.estudiante_listo(modalidad_preferida="PRESENCIAL")
        self.client.force_authenticate(self.perfil.usuario)

    def ids(self, **parametros):
        return [c["id"] for c in self.client.get("/api/v1/convocatorias/", parametros).data["results"]]

    def test_mi_programa_y_ver_todas(self):  # RF-40
        self.assertEqual(self.ids(mi_programa="1"), [self.software.pk])
        self.assertEqual(set(self.ids()), {self.software.pk, self.diseno.pk})

    def test_no_afin_se_ve_pero_no_permite_postularse(self):  # RF-43, RN-05
        datos = self.client.get(f"/api/v1/convocatorias/{self.diseno.pk}/").data["para_estudiante"]
        self.assertFalse(datos["puede_postularse"])
        self.assertEqual(datos["afinidad"]["total"], 0)

    def test_afinidad_completa(self):  # RF-42
        datos = self.client.get(f"/api/v1/convocatorias/{self.software.pk}/").data["para_estudiante"]
        self.assertEqual(datos["afinidad"]["total"], 50 + 35 + 10)  # Sin fecha disponible: 0 puntos de disponibilidad
        self.assertTrue(datos["puede_postularse"])

    def test_busqueda_de_texto_completo_en_espanol(self):
        self.assertEqual(self.ids(q="desarrolladores"), [self.software.pk])  # Coincide por la raíz en español

    def test_recomendadas_excluye_postuladas(self):
        self.assertEqual([c["id"] for c in self.client.get("/api/v1/convocatorias/recomendadas/").data], [self.software.pk])
        self.client.post(URL, {"convocatoria": self.software.pk}, format="json")
        self.assertEqual(self.client.get("/api/v1/convocatorias/recomendadas/").data, [])

    def test_guardar_y_quitar(self):  # RF-44
        self.assertTrue(self.client.post(f"/api/v1/convocatorias/{self.software.pk}/guardar/").data["para_estudiante"]["guardada"])
        self.assertEqual(self.ids(guardadas="1"), [self.software.pk])
        self.client.delete(f"/api/v1/convocatorias/{self.software.pk}/guardar/")
        self.assertEqual(self.ids(guardadas="1"), [])


class AfinidadTests(APITestCase):
    def test_programa_no_afin_da_cero(self):
        datos = pruebas.catalogos()
        empresa, _ = pruebas.empresa()
        convocatoria = pruebas.convocatoria(empresa, [datos["diseno"]])
        self.assertEqual(afinidad.calcular(pruebas.estudiante(), convocatoria)["total"], 0)
