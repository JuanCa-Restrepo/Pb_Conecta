import tempfile

from django.core import mail
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.catalogos.models import Habilidad
from apps.comun import pruebas
from apps.notificaciones.models import Notificacion
from apps.postulaciones.models import Postulacion

URL = "/api/v1/talento/"


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pbconecta-pruebas-"), EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class TalentoTests(APITestCase):
    """RF-45: búsqueda de talento e invitación a postularse."""

    def setUp(self):
        self.datos = pruebas.catalogos()
        self.empresa, self.reclutador = pruebas.empresa()
        self.convocatoria = pruebas.convocatoria(self.empresa, [self.datos["software"]])
        self.visible = pruebas.estudiante_listo(habilidades=("Python", "Django"), abierto_oportunidades=True)
        self.parcial = pruebas.estudiante_listo(habilidades=("Python",), abierto_oportunidades=True)
        self.oculto = pruebas.estudiante_listo(abierto_oportunidades=False)
        self.no_habilitado = pruebas.estudiante(abierto_oportunidades=True)
        self.client.force_authenticate(self.reclutador)

    def ids(self, **parametros):
        return [e["id"] for e in self.client.get(URL, parametros).data["results"]]

    def test_solo_habilitados_abiertos_y_sin_contacto(self):  # RN-10, RF-17
        respuesta = self.client.get(URL)
        self.assertEqual(set(e["id"] for e in respuesta.data["results"]), {self.visible.pk, self.parcial.pk})
        self.assertNotIn("email", respuesta.data["results"][0])
        self.assertNotIn("telefono", respuesta.data["results"][0])
        self.assertNotIn("documento", respuesta.data["results"][0])

    def test_ordena_por_habilidades_coincidentes(self):
        python, django = Habilidad.objects.get(nombre="Python"), Habilidad.objects.get(nombre="Django")
        self.assertEqual(self.ids(habilidades=f"{python.pk},{django.pk}"), [self.visible.pk, self.parcial.pk])
        self.assertEqual(self.ids(habilidades=str(django.pk)), [self.visible.pk])

    def test_solo_empresas_aliadas(self):  # RN-02
        _, vencida = pruebas.empresa(estado="CONVENIO_VENCIDO", convenio_vigente=False)
        self.client.force_authenticate(vencida)
        self.assertEqual(self.client.get(URL).status_code, 403)
        self.client.force_authenticate(self.visible.usuario)
        self.assertEqual(self.client.get(URL).status_code, 403)

    def test_invitar_notifica_una_sola_vez(self):
        url = f"{URL}{self.visible.pk}/invitar/"
        respuesta = self.client.post(url, {"convocatoria": self.convocatoria.pk, "mensaje": "Tu perfil encaja"})
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        aviso = Notificacion.objects.get(usuario=self.visible.usuario, tipo="INVITACION")
        self.assertIn("Tu perfil encaja", aviso.mensaje)
        self.assertEqual(aviso.url_destino, f"/estudiante/convocatorias/{self.convocatoria.pk}")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(self.client.post(url, {"convocatoria": self.convocatoria.pk}).status_code, 400)

    def test_no_invita_a_convocatorias_ajenas_no_afines_o_ya_postuladas(self):
        ajena = pruebas.convocatoria(pruebas.empresa()[0], [self.datos["software"]])
        diseno = pruebas.convocatoria(self.empresa, [self.datos["diseno"]])
        url = f"{URL}{self.visible.pk}/invitar/"
        self.assertEqual(self.client.post(url, {"convocatoria": ajena.pk}).status_code, 400)
        self.assertEqual(self.client.post(url, {"convocatoria": diseno.pk}).status_code, 400)  # RN-05
        Postulacion.objects.create(convocatoria=self.convocatoria, estudiante=self.visible, hoja_vida="protegido/hv/x.pdf")
        self.assertEqual(self.client.post(url, {"convocatoria": self.convocatoria.pk}).status_code, 400)
