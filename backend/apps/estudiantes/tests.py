import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.catalogos.models import Habilidad, PeriodoAcademico
from apps.comun import pruebas
from apps.cuentas.models import Rol
from apps.notificaciones.models import Notificacion

URL = "/api/v1/oficina/estudiantes/"


class HabilitacionTests(APITestCase):
    def setUp(self):
        pruebas.catalogos()
        self.oficina = pruebas.usuario(Rol.OFICINA)
        self.client.force_authenticate(self.oficina)

    def test_estudiante_no_puede_habilitarse(self):  # RN-15
        perfil = pruebas.estudiante()
        self.client.force_authenticate(perfil.usuario)
        self.assertEqual(self.client.post(f"{URL}{perfil.pk}/habilitar/").status_code, 403)

    def test_habilitar_registra_historial_y_notifica(self):  # RF-62, RF-18
        perfil = pruebas.estudiante()
        with self.captureOnCommitCallbacks(execute=True):
            respuesta = self.client.post(f"{URL}{perfil.pk}/habilitar/", {"observacion": "Cumple créditos"})
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.assertEqual(respuesta.data["estado"], "HABILITADO")
        self.assertEqual(respuesta.data["historial"][0]["periodo"], "2026-2")
        self.assertTrue(Notificacion.objects.filter(usuario=perfil.usuario, tipo="HABILITACION").exists())

    def test_no_habilita_dos_veces(self):
        perfil = pruebas.estudiante()
        self.client.post(f"{URL}{perfil.pk}/habilitar/")
        self.assertEqual(self.client.post(f"{URL}{perfil.pk}/habilitar/").status_code, 400)

    def test_deshabilitar_exige_motivo(self):  # RN-11
        perfil = pruebas.estudiante(estado="HABILITADO")
        self.assertEqual(self.client.post(f"{URL}{perfil.pk}/deshabilitar/", {"observacion": ""}).status_code, 400)
        respuesta = self.client.post(f"{URL}{perfil.pk}/deshabilitar/", {"observacion": "Le faltan créditos"})
        self.assertEqual(respuesta.data["estado"], "NO_HABILITADO")

    def test_sin_periodo_vigente_no_se_habilita(self):
        PeriodoAcademico.objects.update(vigente=False)
        perfil = pruebas.estudiante()
        respuesta = self.client.post(f"{URL}{perfil.pk}/habilitar/")
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("periodo", str(respuesta.data["detail"]))

    def test_habilitar_varios_informa_omitidos(self):  # RF-70
        nuevos = [pruebas.estudiante() for _ in range(2)]
        ya_habilitado = pruebas.estudiante(estado="HABILITADO")
        respuesta = self.client.post(f"{URL}habilitar-varios/", {"ids": [p.pk for p in nuevos] + [ya_habilitado.pk]}, format="json")
        self.assertEqual(sorted(respuesta.data["habilitados"]), sorted(p.pk for p in nuevos))
        self.assertEqual([o["id"] for o in respuesta.data["omitidos"]], [ya_habilitado.pk])

    def test_filtros(self):
        pruebas.estudiante(estado="HABILITADO")
        pruebas.estudiante()
        respuesta = self.client.get(URL, {"estado": "NO_HABILITADO"})
        self.assertTrue(all(e["estado"] == "NO_HABILITADO" for e in respuesta.data["results"]))


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pbconecta-pruebas-"))
class PerfilEstudianteTests(APITestCase):
    URL = "/api/v1/estudiantes/yo/"

    def setUp(self):
        pruebas.catalogos()
        self.perfil = pruebas.estudiante()
        self.client.force_authenticate(self.perfil.usuario)

    def test_solo_estudiantes(self):
        self.client.force_authenticate(pruebas.usuario(Rol.OFICINA))
        self.assertEqual(self.client.get(self.URL).status_code, 403)

    def test_editar_datos_y_completitud(self):  # RF-10, RF-15
        inicial = self.client.get(self.URL).data["completitud"]["porcentaje"]
        respuesta = self.client.patch(self.URL, {"telefono": "3001112233", "semestre": 5, "titular": "Desarrolladora web"}, format="json")
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.assertEqual(respuesta.data["telefono"], "3001112233")
        self.assertGreater(respuesta.data["completitud"]["porcentaje"], inicial)

    def test_programa_y_estado_no_se_editan(self):
        otro = pruebas.catalogos()["diseno"]
        self.client.patch(self.URL, {"programa": otro.pk, "estado": "HABILITADO"}, format="json")
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.estado, "NO_HABILITADO")
        self.assertNotEqual(self.perfil.programa_id, otro.pk)

    def test_habilidades_del_catalogo_y_nuevas(self):  # RF-11
        python = Habilidad.objects.create(nombre="Python")
        respuesta = self.client.put(f"{self.URL}habilidades/", {"habilidades": [
            {"habilidad": python.pk, "nivel": "AVANZADO"}, {"nombre": "  Kotlin "}, {"nombre": "python"},
        ]}, format="json")
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.assertEqual(sorted(h["nombre"] for h in respuesta.data["habilidades"]), ["Kotlin", "Python"])
        self.assertTrue(Habilidad.objects.get(nombre="Kotlin").creada_por_usuario)

    def test_hoja_de_vida_solo_pdf_y_protegida(self):  # RF-13, RNF-06
        falso = SimpleUploadedFile("hv.pdf", b"no soy un pdf", content_type="application/pdf")
        self.assertEqual(self.client.post(f"{self.URL}hoja-vida/", {"archivo": falso}).status_code, 400)
        respuesta = self.client.post(f"{self.URL}hoja-vida/", {"archivo": pruebas.pdf()})
        self.assertEqual(respuesta.status_code, 201)
        self.assertTrue(respuesta.data["tiene_hoja_vida"])
        descarga = self.client.get(f"{self.URL}hoja-vida/")
        self.assertTrue(descarga["X-Accel-Redirect"].startswith("/protegido/hv/"))

    def test_secciones_solo_propias(self):
        respuesta = self.client.post(f"{self.URL}idiomas/", {"idioma": "Inglés", "nivel": "B1"})
        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(self.client.post(f"{self.URL}idiomas/", {"idioma": "Inglés", "nivel": "B2"}).status_code, 400)
        otro = pruebas.estudiante()
        self.client.force_authenticate(otro.usuario)
        self.assertEqual(self.client.get(f"{self.URL}idiomas/{respuesta.data['id']}/").status_code, 404)

    def test_experiencia_con_fechas_invertidas(self):
        respuesta = self.client.post(f"{self.URL}experiencias/", {
            "cargo": "Auxiliar", "organizacion": "Tienda", "fecha_inicio": "2025-05-01", "fecha_fin": "2025-01-01",
        })
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("fecha_fin", respuesta.data)
