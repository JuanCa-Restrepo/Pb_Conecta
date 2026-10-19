import tempfile

from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.comun import pruebas
from apps.cuentas.models import Rol
from apps.postulaciones.models import Postulacion, Practica


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix="pbconecta-pruebas-"))
class IndicadoresTests(APITestCase):
    """RF-80 a RF-82."""

    def setUp(self):
        self.datos = pruebas.catalogos()
        self.oficina = pruebas.usuario(Rol.OFICINA)
        self.empresa, self.reclutador = pruebas.empresa()
        self.convocatoria = pruebas.convocatoria(self.empresa, [self.datos["software"]], cupos=3)

        # Dos habilitados de Software (uno ubicado) y uno de Diseño sin habilitar
        self.ubicado = pruebas.estudiante_listo(estado="UBICADO")
        self.ubicado.habilitaciones.create(periodo=self.datos["periodo"], accion="HABILITADO", funcionario=self.oficina)
        self.buscando = pruebas.estudiante_listo()
        pruebas.estudiante(programa=self.datos["diseno"])

        legalizada = Postulacion.objects.create(
            convocatoria=self.convocatoria, estudiante=self.ubicado, hoja_vida="protegido/hv/x.pdf", estado="LEGALIZADO"
        )
        Practica.objects.create(
            postulacion=legalizada, estudiante=self.ubicado, fecha_inicio=timezone.localdate(),
            fecha_fin=timezone.localdate().replace(year=timezone.localdate().year + 1), tipo_vinculacion="PRACTICA",
            asesor_nombre="A", tutor_empresa_nombre="T", legalizada_por=self.oficina,
        )
        Postulacion.objects.create(convocatoria=self.convocatoria, estudiante=self.buscando, hoja_vida="protegido/hv/x.pdf")
        self.client.force_authenticate(self.oficina)

    def test_indicadores_generales(self):
        datos = self.client.get("/api/v1/oficina/indicadores/").data
        self.assertEqual(datos["estudiantes"]["registrados"], 3)
        self.assertEqual(datos["estudiantes"]["habilitados"], 2)
        self.assertEqual(datos["estudiantes"]["ubicados"], 1)
        self.assertEqual(datos["estudiantes"]["en_busqueda"], 1)
        self.assertEqual(datos["estudiantes"]["porcentaje_ubicacion"], 50.0)
        self.assertEqual(datos["oferta"]["cupos_ofertados"], 3)
        self.assertEqual(datos["oferta"]["postulaciones"], 2)
        embudo = {e["estado"]: e["total"] for e in datos["embudo"]}
        self.assertEqual((embudo["POSTULADO"], embudo["LEGALIZADO"]), (1, 1))
        self.assertEqual(datos["tendencia"][-1]["legalizaciones"], 1)

    def test_filtro_por_programa(self):
        datos = self.client.get("/api/v1/oficina/indicadores/", {"programa": self.datos["diseno"].pk}).data
        self.assertEqual(datos["filtros"]["programa"], "Diseño")
        self.assertEqual((datos["estudiantes"]["registrados"], datos["estudiantes"]["habilitados"]), (1, 0))
        self.assertEqual(datos["oferta"]["convocatorias_activas"], 0)

    def test_por_programa(self):
        filas = {f["programa"]: f for f in self.client.get("/api/v1/oficina/indicadores/").data["por_programa"]}
        self.assertEqual(filas["Software"]["porcentaje_ubicacion"], 50.0)
        self.assertEqual(filas["Diseño"]["habilitados"], 0)

    def test_exportar_csv(self):  # RF-81
        respuesta = self.client.get("/api/v1/oficina/exportar/postulaciones.csv")
        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("attachment", respuesta["Content-Disposition"])
        contenido = respuesta.content.decode("utf-8-sig")
        self.assertTrue(contenido.startswith("Estudiante;Programa;Convocatoria"))
        self.assertEqual(len(contenido.strip().splitlines()), 3)  # Encabezado + 2 postulaciones
        for reporte in ("estudiantes", "practicas", "convocatorias", "empresas"):
            self.assertEqual(self.client.get(f"/api/v1/oficina/exportar/{reporte}.csv").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/oficina/exportar/usuarios.csv").status_code, 404)

    def test_solo_la_oficina(self):
        self.client.force_authenticate(self.reclutador)
        self.assertEqual(self.client.get("/api/v1/oficina/indicadores/").status_code, 403)
        self.assertEqual(self.client.get("/api/v1/oficina/exportar/estudiantes.csv").status_code, 403)

    def test_resumen_de_la_empresa(self):  # RF-82
        self.client.force_authenticate(self.reclutador)
        fila = self.client.get("/api/v1/empresas/yo/resumen/").data[0]
        self.assertEqual((fila["total"], fila["por_revisar"], fila["seleccionados"]), (2, 1, 1))
        _, otra = pruebas.empresa()
        self.client.force_authenticate(otra)
        self.assertEqual(self.client.get("/api/v1/empresas/yo/resumen/").data, [])
