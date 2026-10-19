import re

from django.core import mail
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.test import override_settings
from rest_framework.test import APITestCase

from apps.catalogos.models import Facultad, PeriodoAcademico, Programa
from apps.estudiantes.models import Habilitacion, PerfilEstudiante

from .models import Rol, Usuario
from .servicios import SAL_VERIFICACION

CLAVE = "UnaClaveSegura#1"


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DOMINIO_INSTITUCIONAL="pascualbravo.edu.co")
class RegistroEstudianteTests(APITestCase):
    def setUp(self):
        cache.clear()
        facultad = Facultad.objects.create(nombre="Ingeniería")
        self.programa = Programa.objects.create(facultad=facultad, nombre="Software", nivel="TECNOLOGICO")

    def registrar(self, **cambios):
        datos = {"email": "ana@pascualbravo.edu.co", "password": CLAVE, "nombres": "Ana", "apellidos": "Ruiz",
                 "programa": self.programa.pk, "acepta_politica": True, **cambios}
        return self.client.post("/api/v1/auth/registro/estudiante/", datos, format="json")

    def test_rechaza_correo_no_institucional(self):  # RN-01
        respuesta = self.registrar(email="ana@gmail.com")
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("email", respuesta.data)

    def test_exige_aceptar_politica_de_datos(self):  # RF-06
        respuesta = self.registrar(acepta_politica=False)
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("acepta_politica", respuesta.data)

    def test_registro_crea_cuenta_inactiva_no_habilitada_y_envia_correo(self):
        with self.captureOnCommitCallbacks(execute=True):
            respuesta = self.registrar(email="Ana@PascualBravo.edu.co")
        self.assertEqual(respuesta.status_code, 201)
        usuario = Usuario.objects.get(email="ana@pascualbravo.edu.co")  # El correo se guarda en minúsculas
        self.assertFalse(usuario.is_active)
        self.assertEqual(usuario.perfil_estudiante.estado, "NO_HABILITADO")
        self.assertEqual(usuario.consentimientos.count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_no_permite_correo_duplicado(self):
        self.registrar()
        respuesta = self.registrar(email="ANA@pascualbravo.edu.co")
        self.assertEqual(respuesta.status_code, 400)

    def test_verificacion_activa_la_cuenta_y_permite_iniciar_sesion(self):
        from django.core import signing

        self.registrar()
        usuario = Usuario.objects.get(email="ana@pascualbravo.edu.co")
        self.assertEqual(self.client.post("/api/v1/auth/token/", {"email": usuario.email, "password": CLAVE}).status_code, 401)

        token = signing.dumps({"id": usuario.pk}, salt=SAL_VERIFICACION)
        self.assertEqual(self.client.post("/api/v1/auth/verificar-correo/", {"token": token}).status_code, 200)
        respuesta = self.client.post("/api/v1/auth/token/", {"email": usuario.email, "password": CLAVE})
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("access", respuesta.data)


class InicioSesionTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.usuario = Usuario.objects.create_user(
            email="oficina@pascualbravo.edu.co", password=CLAVE, nombres="Laura", apellidos="R", rol=Rol.OFICINA, is_active=True
        )

    def login(self, password):
        return self.client.post("/api/v1/auth/token/", {"email": self.usuario.email, "password": password}).status_code

    def test_los_inicios_exitosos_no_cuentan_para_el_bloqueo(self):  # RNF-07
        self.assertEqual([self.login(CLAVE) for _ in range(7)], [200] * 7)

    def test_bloquea_despues_de_cinco_intentos_fallidos(self):  # RNF-07
        self.assertEqual([self.login("mala") for _ in range(6)], [401] * 5 + [429])
        self.assertEqual(self.login(CLAVE), 429)

    def test_yo_requiere_autenticacion(self):
        self.assertEqual(self.client.get("/api/v1/auth/yo/").status_code, 401)


class RestriccionesBaseDeDatosTests(APITestCase):
    """Las reglas críticas se garantizan también en PostgreSQL (docs/03-modelo-datos.md, sección 4)."""

    def setUp(self):
        facultad = Facultad.objects.create(nombre="Ingeniería")
        programa = Programa.objects.create(facultad=facultad, nombre="Software", nivel="TECNOLOGICO")
        usuario = Usuario.objects.create_user(email="e@pascualbravo.edu.co", password=CLAVE, nombres="E", apellidos="S")
        self.funcionario = Usuario.objects.create_user(email="o@pascualbravo.edu.co", password=CLAVE, nombres="O", apellidos="F", rol=Rol.OFICINA)
        self.estudiante = PerfilEstudiante.objects.create(usuario=usuario, programa=programa)
        self.periodo = PeriodoAcademico.objects.create(codigo="2026-2", fecha_inicio="2026-07-01", fecha_fin="2026-12-01", vigente=True)

    def test_deshabilitar_sin_motivo_falla(self):  # RN-11
        with self.assertRaises(IntegrityError), transaction.atomic():
            Habilitacion.objects.create(estudiante=self.estudiante, periodo=self.periodo, accion="DESHABILITADO", funcionario=self.funcionario)

    def test_estado_invalido_falla(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            PerfilEstudiante.objects.filter(pk=self.estudiante.pk).update(estado="INVENTADO")

    def test_solo_un_periodo_vigente(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            PeriodoAcademico.objects.create(codigo="2027-1", fecha_inicio="2027-01-15", fecha_fin="2027-06-01", vigente=True)


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class ContrasenaTests(APITestCase):
    """RF-05: recuperar y cambiar la contraseña."""

    def setUp(self):
        cache.clear()
        self.usuario = Usuario.objects.create_user(
            email="laura@pascualbravo.edu.co", password=CLAVE, nombres="Laura", apellidos="R", rol=Rol.OFICINA, is_active=True
        )

    def enlace(self):
        cuerpo = mail.outbox[-1].body
        return dict(re.findall(r"(uid|token)=([\w-]+)", cuerpo))

    def test_recuperar_no_revela_si_el_correo_existe(self):
        existente = self.client.post("/api/v1/auth/recuperar/", {"email": "LAURA@pascualbravo.edu.co"})
        inexistente = self.client.post("/api/v1/auth/recuperar/", {"email": "nadie@pascualbravo.edu.co"})
        self.assertEqual(existente.data, inexistente.data)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["laura@pascualbravo.edu.co"])

    def test_restablecer_es_de_un_solo_uso(self):
        self.client.post("/api/v1/auth/recuperar/", {"email": self.usuario.email})
        datos = self.enlace()
        self.assertEqual(self.client.post("/api/v1/auth/restablecer/", {**datos, "password": "123"}).status_code, 400)  # Débil
        self.assertEqual(self.client.post("/api/v1/auth/restablecer/", {**datos, "password": "OtraClave#2026"}).status_code, 200)
        self.assertEqual(self.client.post("/api/v1/auth/token/", {"email": self.usuario.email, "password": "OtraClave#2026"}).status_code, 200)
        self.assertEqual(self.client.post("/api/v1/auth/restablecer/", {**datos, "password": "Tercera#2026x"}).status_code, 400)

    def test_token_falso(self):
        respuesta = self.client.post("/api/v1/auth/restablecer/", {"uid": "MQ", "token": "falso", "password": "OtraClave#2026"})
        self.assertEqual(respuesta.status_code, 400)
        self.assertIn("token", respuesta.data)

    def test_cambiar_clave_exige_la_actual(self):
        self.client.force_authenticate(self.usuario)
        self.assertEqual(self.client.post("/api/v1/auth/cambiar-clave/", {"actual": "mala", "password": "OtraClave#2026"}).status_code, 400)
        self.assertEqual(self.client.post("/api/v1/auth/cambiar-clave/", {"actual": CLAVE, "password": "OtraClave#2026"}).status_code, 200)
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.check_password("OtraClave#2026"))
