import io
import tempfile
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.utils import timezone
from PIL import Image
from rest_framework.test import APITestCase

from apps.comun import pruebas
from apps.cuentas.models import Rol
from apps.notificaciones.models import Notificacion

from .models import Empresa
from .servicios import revisar_convenios

URL = "/api/v1/oficina/empresas/"


class GestionEmpresasTests(APITestCase):
    def setUp(self):
        self.datos = pruebas.catalogos()
        self.oficina = pruebas.usuario(Rol.OFICINA)
        self.client.force_authenticate(self.oficina)
        self.hoy = timezone.localdate()

    def convenio(self, **cambios):
        return {"numero": "CONV-NUEVO", "fecha_inicio": self.hoy - timedelta(days=1), "fecha_fin": self.hoy + timedelta(days=365), **cambios}

    def test_solo_la_oficina_puede_gestionar_empresas(self):
        _, reclutador = pruebas.empresa()
        self.client.force_authenticate(reclutador)
        self.assertEqual(self.client.get(URL).status_code, 403)

    def test_aprobar_registra_convenio_y_notifica(self):  # RF-60, RF-25
        empresa, reclutador = pruebas.empresa(estado=Empresa.Estado.PENDIENTE)
        with self.captureOnCommitCallbacks(execute=True):
            respuesta = self.client.post(f"{URL}{empresa.pk}/aprobar/", self.convenio())
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.assertEqual(respuesta.data["estado"], "ALIADA")
        self.assertTrue(respuesta.data["puede_publicar"])
        self.assertTrue(Notificacion.objects.filter(usuario=reclutador, tipo="EMPRESA_APROBADA").exists())

    def test_no_aprueba_con_convenio_que_no_esta_vigente(self):
        empresa, _ = pruebas.empresa(estado=Empresa.Estado.PENDIENTE)
        respuesta = self.client.post(f"{URL}{empresa.pk}/aprobar/", self.convenio(fecha_inicio=self.hoy + timedelta(days=10)))
        self.assertEqual(respuesta.status_code, 400)
        empresa.refresh_from_db()
        self.assertEqual(empresa.estado, "PENDIENTE")
        self.assertFalse(empresa.convenios.exists())  # La transacción se revierte

    def test_rechazar_exige_motivo(self):  # RN-11
        empresa, _ = pruebas.empresa(estado=Empresa.Estado.PENDIENTE)
        self.assertEqual(self.client.post(f"{URL}{empresa.pk}/rechazar/", {"motivo": " "}).status_code, 400)
        respuesta = self.client.post(f"{URL}{empresa.pk}/rechazar/", {"motivo": "NIT no corresponde"})
        self.assertEqual(respuesta.data["estado"], "RECHAZADA")

    def test_transicion_invalida(self):  # RN-13
        empresa, _ = pruebas.empresa()
        self.assertEqual(self.client.post(f"{URL}{empresa.pk}/rechazar/", {"motivo": "x"}).status_code, 400)

    def test_documento_debe_ser_pdf(self):  # RNF-06
        empresa, _ = pruebas.empresa(estado=Empresa.Estado.PENDIENTE)
        falso = SimpleUploadedFile("convenio.pdf", b"esto no es un pdf", content_type="application/pdf")
        respuesta = self.client.post(f"{URL}{empresa.pk}/aprobar/", {**self.convenio(), "documento": falso})
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("documento", respuesta.data)

    def test_convenio_vencido_y_renovacion(self):  # RN-02, RF-26
        empresa, _ = pruebas.empresa(convenio_vigente=False)
        revisar_convenios()
        empresa.refresh_from_db()
        self.assertEqual(empresa.estado, "CONVENIO_VENCIDO")
        self.assertFalse(empresa.puede_publicar)

        respuesta = self.client.post(f"{URL}{empresa.pk}/convenios/", self.convenio(numero="CONV-RENOVADO"))
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        self.assertEqual(respuesta.data["estado"], "ALIADA")

    def test_oficina_crea_empresa_con_convenio(self):  # RF-24
        respuesta = self.client.post(URL, {
            "razon_social": "Nueva S.A.S.", "nit": "901222333-4", "sector": self.datos["sector"].pk,
            "ciudad": self.datos["ciudad"].pk, "contacto_nombre": "Ana", "contacto_email": "ana@nueva.example",
            **self.convenio(numero="CONV-OF-1"),
        })
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        self.assertEqual(respuesta.data["estado"], "ALIADA")
        self.assertTrue(respuesta.data["creada_por_oficina"])


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pbconecta-pruebas-"))
class DirectorioEmpresasTests(APITestCase):
    """RF-20 a RF-23: directorio público, página de la empresa, seguir y perfil propio."""

    def setUp(self):
        self.datos = pruebas.catalogos()
        self.empresa, self.reclutador = pruebas.empresa()
        self.pendiente, _ = pruebas.empresa(estado=Empresa.Estado.PENDIENTE)
        self.convocatoria = pruebas.convocatoria(self.empresa, [self.datos["software"]])

    def test_directorio_publico_solo_aliadas_y_sin_contacto(self):
        respuesta = self.client.get("/api/v1/empresas/")  # Sin iniciar sesión
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual([e["id"] for e in respuesta.data["results"]], [self.empresa.pk])
        self.assertEqual(respuesta.data["results"][0]["convocatorias_activas"], 1)
        self.assertNotIn("contacto_email", respuesta.data["results"][0])
        self.assertNotIn("nit", respuesta.data["results"][0])
        self.assertEqual(self.client.get(f"/api/v1/empresas/{self.pendiente.pk}/").status_code, 404)

    def test_pagina_con_convocatorias_publicadas(self):  # RF-22
        pagina = self.client.get(f"/api/v1/empresas/{self.empresa.pk}/").data
        self.assertEqual([c["id"] for c in pagina["convocatorias"]], [self.convocatoria.pk])

    def test_seguir_y_aviso_de_nueva_convocatoria(self):  # RF-23
        diseno = pruebas.estudiante(programa=self.datos["diseno"])  # No es de un programa afín
        self.client.force_authenticate(diseno.usuario)
        self.assertTrue(self.client.post(f"/api/v1/empresas/{self.empresa.pk}/seguir/").data["seguida"])
        self.assertEqual(len(self.client.get("/api/v1/empresas/", {"seguidas": "1"}).data["results"]), 1)
        with self.captureOnCommitCallbacks(execute=True):
            pruebas.convocatoria(self.empresa, [self.datos["software"]], titulo="Nueva vacante")
        self.assertTrue(Notificacion.objects.filter(usuario=diseno.usuario, tipo="CONVOCATORIA_NUEVA").exists())
        self.client.force_authenticate(self.reclutador)
        self.assertEqual(self.client.post(f"/api/v1/empresas/{self.empresa.pk}/seguir/").status_code, 403)

    def test_aviso_a_habilitados_de_programas_afines(self):  # M9
        habilitado = pruebas.estudiante(estado="HABILITADO")
        no_habilitado = pruebas.estudiante()
        with self.captureOnCommitCallbacks(execute=True):
            pruebas.convocatoria(self.empresa, [self.datos["software"]])
        self.assertTrue(Notificacion.objects.filter(usuario=habilitado.usuario, tipo="CONVOCATORIA_NUEVA").exists())
        self.assertFalse(Notificacion.objects.filter(usuario=no_habilitado.usuario, tipo="CONVOCATORIA_NUEVA").exists())

    def test_perfil_propio_y_logo(self):  # RF-20
        self.client.force_authenticate(self.reclutador)
        respuesta = self.client.patch("/api/v1/empresas/yo/", {"descripcion": "Software para logística", "razon_social": "Otra"}, format="json")
        self.assertEqual(respuesta.data["descripcion"], "Software para logística")
        self.assertNotEqual(respuesta.data["razon_social"], "Otra")  # Dato legal: solo la oficina
        falso = SimpleUploadedFile("logo.png", b"no es imagen", content_type="image/png")
        self.assertEqual(self.client.post("/api/v1/empresas/yo/logo/", {"logo": falso}).status_code, 400)
        contenido = io.BytesIO()
        Image.new("RGB", (8, 8), "navy").save(contenido, format="PNG")
        logo = SimpleUploadedFile("logo.png", contenido.getvalue(), content_type="image/png")
        self.assertTrue(self.client.post("/api/v1/empresas/yo/logo/", {"logo": logo}).data["logo"].startswith("/media/publico/logos/"))
