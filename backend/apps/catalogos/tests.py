import tempfile

from django.core.management import call_command
from django.test import TestCase, override_settings

from apps.convocatorias.models import Convocatoria
from apps.cuentas.models import Usuario
from apps.estudiantes.models import PerfilEstudiante
from apps.postulaciones import servicios as servicios_postulacion


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pbconecta-pruebas-"), EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class CargarDemoTests(TestCase):
    """RNF-15: la demostración arranca lista desde una base de datos vacía."""

    def test_carga_completa_e_idempotente(self):
        call_command("cargar_demo", verbosity=0)
        self.assertEqual(Usuario.objects.count(), 6)  # Uno por rol + estudiante no habilitado + empresa pendiente
        self.assertEqual(Convocatoria.objects.filter(estado="PUBLICADA").count(), 3)

        camila = PerfilEstudiante.objects.get(usuario__email="estudiante@pascualbravo.edu.co")
        self.assertTrue(camila.hoja_vida.read(5) == b"%PDF-")
        self.assertIsNone(servicios_postulacion.motivo_perfil(camila))  # Lista para postularse en la demo

        call_command("cargar_demo", verbosity=0)  # Segunda ejecución: no duplica nada
        self.assertEqual(Usuario.objects.count(), 6)  # Uno por rol + estudiante no habilitado + empresa pendiente
