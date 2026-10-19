from datetime import timedelta

from django.utils import timezone
from rest_framework.test import APITestCase

from apps.comun import pruebas
from apps.cuentas.models import Rol
from apps.muro.models import Publicacion
from apps.notificaciones.models import Notificacion

from .models import Convocatoria

URL = "/api/v1/convocatorias/"


class FlujoConvocatoriaTests(APITestCase):
    def setUp(self):
        self.datos = pruebas.catalogos()
        self.oficina = pruebas.usuario(Rol.OFICINA)
        self.empresa, self.reclutador = pruebas.empresa()
        self.client.force_authenticate(self.reclutador)

    def cuerpo(self, **cambios):
        hoy = timezone.localdate()
        return {
            "titulo": "Practicante de desarrollo", "descripcion": "Desarrollo web", "funciones": "Programar",
            "modalidad": "PRESENCIAL", "ciudad": self.datos["ciudad"].pk, "tipo_vinculacion": "PRACTICA",
            "cupos": 2, "fecha_inicio": hoy + timedelta(days=60), "duracion_meses": 6,
            "fecha_cierre": hoy + timedelta(days=20), "programas": [self.datos["software"].pk], **cambios,
        }

    def crear(self, **cambios):
        respuesta = self.client.post(URL, self.cuerpo(**cambios), format="json")
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        return respuesta.data

    def test_flujo_completo_devolver_y_aprobar(self):  # RN-03, escenario 2
        convocatoria = self.crear()
        self.assertEqual(convocatoria["estado"], "BORRADOR")
        self.assertIn("enviar_revision", convocatoria["acciones"])

        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(self.client.post(f"{URL}{convocatoria['id']}/enviar-revision/").data["estado"], "EN_REVISION")
        self.assertTrue(Notificacion.objects.filter(usuario=self.oficina, tipo="CONVOCATORIA_REVISION").exists())

        # La empresa no puede aprobarse a sí misma
        self.assertEqual(self.client.post(f"{URL}{convocatoria['id']}/aprobar/").status_code, 400)

        self.client.force_authenticate(self.oficina)
        self.assertEqual(self.client.post(f"{URL}{convocatoria['id']}/devolver/", {"observacion": ""}).status_code, 400)
        devuelta = self.client.post(f"{URL}{convocatoria['id']}/devolver/", {"observacion": "Indica el horario"}).data
        self.assertEqual(devuelta["estado"], "DEVUELTA")

        self.client.force_authenticate(self.reclutador)
        self.client.patch(f"{URL}{convocatoria['id']}/", {"funciones": "Programar de 8 a 5"}, format="json")
        self.client.post(f"{URL}{convocatoria['id']}/enviar-revision/")

        self.client.force_authenticate(self.oficina)
        publicada = self.client.post(f"{URL}{convocatoria['id']}/aprobar/").data
        self.assertEqual(publicada["estado"], "PUBLICADA")
        self.assertEqual(publicada["observacion_revision"], "")
        self.assertTrue(Publicacion.objects.filter(convocatoria_id=convocatoria["id"], tipo="CONVOCATORIA").exists())  # RF-35

    def test_programas_obligatorios(self):  # RF-30
        respuesta = self.client.post(URL, self.cuerpo(programas=[]), format="json")
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("programas", respuesta.data)

    def test_ciudad_obligatoria_si_no_es_remota(self):
        self.assertEqual(self.client.post(URL, self.cuerpo(ciudad=None), format="json").status_code, 400)
        self.assertEqual(self.client.post(URL, self.cuerpo(ciudad=None, modalidad="REMOTA"), format="json").status_code, 201)

    def test_empresa_sin_convenio_vigente_no_crea(self):  # RN-02
        _, reclutador = pruebas.empresa(estado="CONVENIO_VENCIDO", convenio_vigente=False)
        self.client.force_authenticate(reclutador)
        self.assertEqual(self.client.post(URL, self.cuerpo(), format="json").status_code, 403)

    def test_empresa_no_ve_convocatorias_de_otra(self):  # RNF-05, escenario 7
        ajena = self.crear()
        _, otro = pruebas.empresa()
        self.client.force_authenticate(otro)
        self.assertEqual(self.client.get(f"{URL}{ajena['id']}/").status_code, 404)
        self.assertEqual(self.client.get(URL).data["count"], 0)

    def test_estudiante_solo_ve_publicadas_y_no_modifica(self):
        borrador = self.crear()
        estudiante = pruebas.estudiante()
        self.client.force_authenticate(estudiante.usuario)
        self.assertEqual(self.client.get(f"{URL}{borrador['id']}/").status_code, 404)
        self.assertEqual(self.client.post(URL, self.cuerpo(), format="json").status_code, 403)

    def test_oficina_publica_directamente_en_nombre_de_empresa(self):  # RF-31, RN-03
        self.client.force_authenticate(self.oficina)
        sin_empresa = self.client.post(URL, self.cuerpo(), format="json")
        self.assertEqual(sin_empresa.status_code, 400)
        creada = self.client.post(URL, self.cuerpo(empresa=self.empresa.pk), format="json").data
        self.assertIn("aprobar", creada["acciones"])
        self.assertEqual(self.client.post(f"{URL}{creada['id']}/aprobar/").data["estado"], "PUBLICADA")

    def test_editar_publicada_vuelve_a_revision(self):  # RF-33
        convocatoria = Convocatoria.objects.get(pk=self.crear()["id"])
        convocatoria.estado = "PUBLICADA"
        convocatoria.save()
        respuesta = self.client.patch(f"{URL}{convocatoria.pk}/", {"cupos": 3}, format="json")
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        convocatoria.refresh_from_db()
        self.assertEqual(convocatoria.estado, "EN_REVISION")

    def test_no_edita_en_revision_ni_cerrada(self):
        convocatoria = self.crear()
        self.client.post(f"{URL}{convocatoria['id']}/enviar-revision/")
        self.assertEqual(self.client.patch(f"{URL}{convocatoria['id']}/", {"cupos": 5}, format="json").status_code, 403)

    def test_duplicar_crea_borrador(self):
        original = self.crear()
        copia = self.client.post(f"{URL}{original['id']}/duplicar/").data
        self.assertEqual(copia["estado"], "BORRADOR")
        self.assertEqual(copia["programas"], original["programas"])
        self.assertNotEqual(copia["id"], original["id"])
