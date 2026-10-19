import tempfile
from datetime import timedelta

from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.comun import pruebas
from apps.cuentas.models import Rol
from apps.notificaciones.models import Notificacion
from apps.reportes import alertas

from .models import Postulacion, Practica
from .practicas import iniciar_practicas

URL = "/api/v1/postulaciones/"


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pbconecta-pruebas-"))
class LegalizacionTests(APITestCase):
    """Escenario 5: verificación en persona, legalización y cierre automático de lo demás."""

    def setUp(self):
        self.datos = pruebas.catalogos()
        self.oficina = pruebas.usuario(Rol.OFICINA)
        self.empresa, self.reclutador = pruebas.empresa()
        self.convocatoria = pruebas.convocatoria(self.empresa, [self.datos["software"]], cupos=1)
        self.otra = pruebas.convocatoria(pruebas.empresa()[0], [self.datos["software"]])
        self.perfil = pruebas.estudiante_listo()
        self.postulacion = self.seleccionar(self.convocatoria)
        self.otra_postulacion = Postulacion.objects.create(
            convocatoria=self.otra, estudiante=self.perfil, hoja_vida="protegido/hv/x.pdf", afinidad=50
        )
        self.client.force_authenticate(self.oficina)

    def seleccionar(self, convocatoria):
        postulacion = Postulacion.objects.create(
            convocatoria=convocatoria, estudiante=self.perfil, hoja_vida="protegido/hv/x.pdf", afinidad=80, estado="SELECCIONADO"
        )
        return postulacion

    def verificar(self, resultado="CUMPLE", observacion=""):
        return self.client.post(f"{URL}{self.postulacion.pk}/verificar/", {"resultado": resultado, "observacion": observacion}, format="json")

    def legalizar(self, inicio_en_dias=10, **cambios):
        hoy = timezone.localdate()
        datos = {
            "fecha_inicio": hoy + timedelta(days=inicio_en_dias), "fecha_fin": hoy + timedelta(days=inicio_en_dias + 180),
            "tipo_vinculacion": "PRACTICA", "asesor_nombre": "Docente Asesor", "tutor_empresa_nombre": "Tutor Empresa", **cambios,
        }
        return self.client.post(f"{URL}{self.postulacion.pk}/legalizar/", datos)

    # ---------------------------------------------------------------- verificación y permisos
    def test_solo_la_oficina_verifica_y_legaliza(self):
        self.client.force_authenticate(self.reclutador)
        self.assertEqual(self.verificar().status_code, 403)
        self.assertEqual(self.legalizar().status_code, 403)

    def test_no_cumple_exige_observacion_y_avisa_al_estudiante(self):  # RN-11
        self.assertEqual(self.verificar("NO_CUMPLE").status_code, 400)
        with self.captureOnCommitCallbacks(execute=True):
            respuesta = self.verificar("NO_CUMPLE", "Falta el curso de preparación")
        self.assertEqual(respuesta.status_code, 200, respuesta.data)
        self.assertFalse(respuesta.data["acciones"]["legalizar"])
        self.assertTrue(Notificacion.objects.filter(usuario=self.perfil.usuario, tipo="VERIFICACION_NO_CUMPLE").exists())

    def test_sin_verificacion_cumple_no_se_legaliza(self):  # RN-07
        self.assertEqual(self.legalizar().status_code, 400)
        self.verificar("NO_CUMPLE", "Pendiente")
        self.assertEqual(self.legalizar().status_code, 400)
        self.verificar("CUMPLE")  # La última verificación es la que cuenta
        self.assertEqual(self.legalizar().status_code, 201)

    def test_verificaciones_solo_visibles_para_la_oficina(self):
        self.verificar("NO_CUMPLE", "Pendiente")
        self.client.force_authenticate(self.perfil.usuario)
        self.assertEqual(self.client.get(f"{URL}{self.postulacion.pk}/").data["verificaciones"], [])

    # ---------------------------------------------------------------- legalización
    def test_legalizar_ubica_cierra_otras_postulaciones_y_la_convocatoria(self):  # RF-64, RN-08, RN-09
        self.verificar()
        with self.captureOnCommitCallbacks(execute=True):
            respuesta = self.legalizar(documento_soporte=pruebas.pdf("acta.pdf"))
        self.assertEqual(respuesta.status_code, 201, respuesta.data)
        self.assertEqual(respuesta.data["estado"], "LEGALIZADO")
        self.assertEqual(respuesta.data["practica"]["estado"], "LEGALIZADA")
        self.assertTrue(respuesta.data["practica"]["tiene_documento"])

        self.perfil.refresh_from_db()
        self.otra_postulacion.refresh_from_db()
        self.convocatoria.refresh_from_db()
        self.assertEqual(self.perfil.estado, "UBICADO")
        self.assertEqual(self.otra_postulacion.estado, "CERRADO_SISTEMA")
        self.assertEqual(self.otra_postulacion.historial.last().estado_nuevo, "CERRADO_SISTEMA")
        self.assertEqual((self.convocatoria.estado, self.convocatoria.motivo_cierre), ("CERRADA", "CUPOS"))  # cupos=1
        self.assertTrue(Notificacion.objects.filter(usuario=self.reclutador, tipo="PRACTICA_LEGALIZADA").exists())

    def test_legalizar_con_inicio_hoy_queda_en_curso(self):
        self.verificar()
        self.legalizar(inicio_en_dias=0)
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.estado, "EN_PRACTICA")
        self.assertEqual(Practica.objects.get().estado, "EN_CURSO")

    def test_ubicado_no_puede_postularse_a_otras(self):  # RN-08
        self.verificar()
        self.legalizar()
        nueva = pruebas.convocatoria(self.empresa, [self.datos["software"]])
        self.client.force_authenticate(self.perfil.usuario)
        respuesta = self.client.post(URL, {"convocatoria": nueva.pk}, format="json")
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("RN-08", str(respuesta.data["detail"]))

    def test_fechas_invertidas(self):
        self.verificar()
        hoy = timezone.localdate()
        self.assertEqual(self.legalizar(fecha_fin=hoy).status_code, 400)

    # ---------------------------------------------------------------- ciclo de vida de la práctica
    def test_iniciar_finalizar_y_visibilidad(self):  # RF-65
        self.verificar()
        practica_id = self.legalizar(inicio_en_dias=5).data["practica"]["id"]
        self.assertEqual(iniciar_practicas(hoy=timezone.localdate() + timedelta(days=5)), 1)
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.estado, "EN_PRACTICA")

        self.assertEqual(self.client.post(f"/api/v1/practicas/{practica_id}/finalizar/", {"observacion": ""}).status_code, 400)
        respuesta = self.client.post(f"/api/v1/practicas/{practica_id}/finalizar/", {"observacion": "Evaluación satisfactoria"})
        self.assertEqual(respuesta.data["estado"], "FINALIZADA")
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.estado, "PRACTICA_FINALIZADA")

        self.client.force_authenticate(self.perfil.usuario)  # El estudiante ve la suya pero no la gestiona
        self.assertEqual(self.client.get("/api/v1/practicas/").data["count"], 1)
        self.assertEqual(self.client.post(f"/api/v1/practicas/{practica_id}/cancelar/", {"observacion": "x"}).status_code, 403)
        self.client.force_authenticate(pruebas.empresa()[1])  # Otra empresa no la ve
        self.assertEqual(self.client.get(f"/api/v1/practicas/{practica_id}/").status_code, 404)

    def test_cancelar_devuelve_al_estudiante_a_habilitado(self):  # RN-08
        self.verificar()
        practica_id = self.legalizar().data["practica"]["id"]
        self.assertEqual(self.client.post(f"/api/v1/practicas/{practica_id}/cancelar/", {"observacion": ""}).status_code, 400)
        self.client.post(f"/api/v1/practicas/{practica_id}/cancelar/", {"observacion": "La empresa canceló el cupo"})
        self.perfil.refresh_from_db()
        self.assertEqual(self.perfil.estado, "HABILITADO")


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pbconecta-pruebas-"))
class AlertasTests(APITestCase):
    """RF-66: alertas de seguimiento de la oficina."""

    def setUp(self):
        self.datos = pruebas.catalogos()
        self.oficina = pruebas.usuario(Rol.OFICINA)
        self.empresa, _ = pruebas.empresa()

    def categoria(self, clave):
        return next(c for c in alertas.calcular()["categorias"] if c["clave"] == clave)

    def test_categorias(self):
        hace_mucho = timezone.now() - timedelta(days=90)
        perfil = pruebas.estudiante_listo()
        perfil.habilitaciones.create(periodo=self.datos["periodo"], accion="HABILITADO", funcionario=self.oficina)
        perfil.habilitaciones.update(creado_en=hace_mucho)
        self.assertEqual([i["id"] for i in self.categoria("sin_postular")["items"]], [perfil.id])

        convocatoria = pruebas.convocatoria(self.empresa, [self.datos["software"]])
        Convocatoria = type(convocatoria)
        Convocatoria.objects.filter(pk=convocatoria.pk).update(publicada_en=hace_mucho)
        self.assertEqual(self.categoria("convocatorias_sin_postulantes")["total"], 1)

        postulacion = Postulacion.objects.create(convocatoria=convocatoria, estudiante=perfil, hoja_vida="protegido/hv/x.pdf")
        Postulacion.objects.filter(pk=postulacion.pk).update(creado_en=hace_mucho)
        self.assertEqual(self.categoria("sin_respuesta")["total"], 1)
        self.assertEqual(self.categoria("sin_ubicar")["total"], 1)
        self.assertEqual(self.categoria("sin_postular")["total"], 0)
        self.assertEqual(self.categoria("convocatorias_sin_postulantes")["total"], 0)

        Postulacion.objects.filter(pk=postulacion.pk).update(estado="SELECCIONADO")
        self.assertEqual(self.categoria("por_legalizar")["total"], 1)

    def test_endpoint_solo_oficina_y_aviso_diario_idempotente(self):
        perfil = pruebas.estudiante_listo()
        convocatoria = pruebas.convocatoria(self.empresa, [self.datos["software"]])
        Postulacion.objects.create(convocatoria=convocatoria, estudiante=perfil, hoja_vida="protegido/hv/x.pdf", estado="SELECCIONADO")

        self.client.force_authenticate(perfil.usuario)
        self.assertEqual(self.client.get("/api/v1/oficina/alertas/").status_code, 403)
        self.client.force_authenticate(self.oficina)
        self.assertGreaterEqual(self.client.get("/api/v1/oficina/alertas/").data["total"], 1)

        with self.settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            call_command("generar_alertas", verbosity=0)
            call_command("generar_alertas", verbosity=0)
        self.assertEqual(Notificacion.objects.filter(usuario=self.oficina, tipo="ALERTAS_DIARIAS").count(), 1)

    def test_notas_de_asesoria(self):  # RF-67
        perfil = pruebas.estudiante()
        self.client.force_authenticate(self.oficina)
        respuesta = self.client.post(f"/api/v1/oficina/estudiantes/{perfil.pk}/notas/", {"texto": "Se le recomendó ajustar la HV"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.data[0]["texto"], "Se le recomendó ajustar la HV")
        self.client.force_authenticate(perfil.usuario)
        self.assertEqual(self.client.get(f"/api/v1/oficina/estudiantes/{perfil.pk}/notas/").status_code, 403)
