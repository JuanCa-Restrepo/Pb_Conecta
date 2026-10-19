"""Carga catálogos y datos de demostración (RNF-15). Solo actúa si la base de datos no tiene usuarios.

Las credenciales de prueba están documentadas en el README del proyecto.
"""

from datetime import date, timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.catalogos.models import Ciudad, Facultad, Habilidad, Parametro, PeriodoAcademico, Programa, Sector
from apps.convocatorias.models import Convocatoria
from apps.convocatorias.servicios import publicar
from apps.cuentas.models import Rol, Usuario
from apps.empresas.models import Convenio, Empresa, UsuarioEmpresa
from apps.estudiantes.models import EstadoEstudiante, EstudianteHabilidad, Habilitacion, PerfilEstudiante
from apps.muro.models import Publicacion

CLAVE_DEMO = "PbConecta2026*"

# Catálogo inicial de programas. Verificar contra la oferta académica oficial del Pascual Bravo.
PROGRAMAS = {
    "Facultad de Ingeniería": [
        ("Tecnología en Desarrollo de Software", "TECNOLOGICO"),
        ("Ingeniería de Software", "PROFESIONAL"),
        ("Tecnología en Electrónica Industrial", "TECNOLOGICO"),
        ("Tecnología en Electricidad", "TECNOLOGICO"),
        ("Ingeniería Eléctrica", "PROFESIONAL"),
        ("Tecnología Mecánica Industrial", "TECNOLOGICO"),
        ("Ingeniería Mecánica", "PROFESIONAL"),
        ("Ingeniería Industrial", "PROFESIONAL"),
    ],
    "Facultad de Producción y Diseño": [
        ("Tecnología en Diseño Textil y Producción de Modas", "TECNOLOGICO"),
        ("Diseño Gráfico", "PROFESIONAL"),
        ("Tecnología en Gestión del Diseño Gráfico", "TECNOLOGICO"),
    ],
    "Facultad de Artes y Humanidades": [
        ("Tecnología en Gestión Cultural", "TECNOLOGICO"),
    ],
}

HABILIDADES_TECNICAS = [
    "Python", "Django", "JavaScript", "TypeScript", "React", "SQL", "PostgreSQL", "Git", "Docker", "Java",
    "Excel avanzado", "AutoCAD", "SolidWorks", "PLC", "Electrónica digital", "Instalaciones eléctricas",
    "Adobe Illustrator", "Adobe Photoshop", "Figma", "Patronaje", "Lean Manufacturing",
]
HABILIDADES_BLANDAS = ["Trabajo en equipo", "Comunicación asertiva", "Resolución de problemas", "Adaptabilidad"]
SECTORES = ["Tecnología", "Manufactura", "Energía", "Textil y confección", "Comunicación y diseño", "Servicios", "Sector público"]
CIUDADES = [
    ("Medellín", "Antioquia"), ("Bello", "Antioquia"), ("Itagüí", "Antioquia"), ("Envigado", "Antioquia"),
    ("Sabaneta", "Antioquia"), ("Rionegro", "Antioquia"), ("Bogotá", "Cundinamarca"),
]
PARAMETROS = [
    ("dias_sin_postular", "15", "Alerta: estudiante habilitado sin postulaciones después de estos días"),
    ("dias_sin_respuesta", "10", "Alerta: postulación sin respuesta de la empresa después de estos días"),
    ("dias_sin_ubicar", "60", "Alerta: estudiante sin ubicar después de estos días desde su primera postulación"),
    ("dias_aviso_convenio", "30", "Aviso a la oficina cuando un convenio vence en estos días"),
    ("dias_convocatoria_sin_postulantes", "7", "Alerta: convocatoria publicada sin postulantes después de estos días"),
]


def pdf_de_ejemplo(lineas):
    """PDF de una página con texto (Helvetica), para que la hoja de vida de demostración se pueda abrir y leer."""

    def escapar(texto):
        return texto.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    contenido = "BT /F1 12 Tf 72 760 Td 16 TL " + " ".join(f"({escapar(linea)}) '" for linea in lineas) + " ET"
    flujo = contenido.encode("latin-1")
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(flujo)).encode() + b" >>\nstream\n" + flujo + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
    ]
    salida, posiciones = bytearray(b"%PDF-1.4\n"), []
    for numero, cuerpo in enumerate(objetos, start=1):
        posiciones.append(len(salida))
        salida += f"{numero} 0 obj\n".encode() + cuerpo + b"\nendobj\n"
    inicio_xref = len(salida)
    salida += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode()
    salida += b"".join(f"{posicion:010d} 00000 n \n".encode() for posicion in posiciones)
    salida += f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{inicio_xref}\n%%EOF\n".encode()
    return bytes(salida)


class Command(BaseCommand):
    help = "Carga catálogos y datos de demostración si la base de datos está vacía."

    def add_arguments(self, parser):
        parser.add_argument("--forzar", action="store_true", help="Cargar aunque ya existan usuarios")

    @transaction.atomic
    def handle(self, *args, **opciones):
        if Usuario.objects.exists() and not opciones["forzar"]:
            self.stdout.write("[demo] La base de datos ya tiene usuarios: no se cargan datos de demostración.")
            return

        self._catalogos()
        usuarios = self._usuarios()
        self._empresas_y_convocatorias(usuarios)
        self._muro(usuarios["oficina"])
        self.stdout.write(self.style.SUCCESS("[demo] Datos de demostración cargados. Credenciales en el README."))

    # ------------------------------------------------------------------ catálogos
    def _catalogos(self):
        for nombre_facultad, programas in PROGRAMAS.items():
            facultad, _ = Facultad.objects.get_or_create(nombre=nombre_facultad)
            for nombre, nivel in programas:
                Programa.objects.get_or_create(nombre=nombre, nivel=nivel, defaults={"facultad": facultad})
        for nombre in HABILIDADES_TECNICAS:
            Habilidad.objects.get_or_create(nombre=nombre, defaults={"tipo": Habilidad.Tipo.TECNICA})
        for nombre in HABILIDADES_BLANDAS:
            Habilidad.objects.get_or_create(nombre=nombre, defaults={"tipo": Habilidad.Tipo.BLANDA})
        for nombre in SECTORES:
            Sector.objects.get_or_create(nombre=nombre)
        for nombre, departamento in CIUDADES:
            Ciudad.objects.get_or_create(nombre=nombre, departamento=departamento)
        for clave, valor, descripcion in PARAMETROS:
            Parametro.objects.get_or_create(clave=clave, defaults={"valor": valor, "descripcion": descripcion})
        PeriodoAcademico.objects.get_or_create(
            codigo="2026-2", defaults={"fecha_inicio": date(2026, 7, 21), "fecha_fin": date(2026, 12, 12), "vigente": True}
        )

    # ------------------------------------------------------------------ usuarios
    def _usuario(self, email, nombres, apellidos, rol, **extra):
        return Usuario.objects.create_user(
            email=email, password=CLAVE_DEMO, nombres=nombres, apellidos=apellidos, rol=rol,
            is_active=True, email_verificado_en=timezone.now(), **extra,
        )

    def _usuarios(self):
        dominio = "pascualbravo.edu.co"
        admin = Usuario.objects.create_superuser(
            email=f"admin@{dominio}", password=CLAVE_DEMO, nombres="Super", apellidos="Administrador",
            email_verificado_en=timezone.now(),
        )
        oficina = self._usuario(f"practicas@{dominio}", "Laura", "Restrepo", Rol.OFICINA, telefono="6044480520")

        software = Programa.objects.get(nombre="Tecnología en Desarrollo de Software")
        diseno = Programa.objects.get(nombre="Diseño Gráfico")
        periodo = PeriodoAcademico.actual()

        # Estudiante habilitado (puede postularse)
        u1 = self._usuario(f"estudiante@{dominio}", "Camila", "Gómez", Rol.ESTUDIANTE, telefono="3001234567")
        e1 = PerfilEstudiante.objects.create(
            usuario=u1, programa=software, semestre=5, titular="Estudiante de Software · React y Django",
            acerca_de="Me interesa el desarrollo web y las bases de datos.", modalidad_preferida="HIBRIDA",
            jornada="COMPLETA", fecha_disponible=date(2027, 1, 15), abierto_oportunidades=True,
            estado=EstadoEstudiante.HABILITADO,
        )
        for nombre, nivel in [("Python", "INTERMEDIO"), ("React", "BASICO"), ("SQL", "INTERMEDIO"), ("Git", "INTERMEDIO")]:
            EstudianteHabilidad.objects.create(estudiante=e1, habilidad=Habilidad.objects.get(nombre=nombre), nivel=nivel)
        Habilitacion.objects.create(
            estudiante=e1, periodo=periodo, accion=Habilitacion.Accion.HABILITADO, funcionario=oficina,
            observacion="Cumple créditos y curso de preparación para la práctica.",
        )
        e1.hoja_vida.save("hoja-vida.pdf", ContentFile(pdf_de_ejemplo([
            "Camila Gómez - Hoja de vida (ejemplo de demostración)",
            "Tecnología en Desarrollo de Software - Institución Universitaria Pascual Bravo",
            "Correo: estudiante@pascualbravo.edu.co - Teléfono: 300 123 4567",
            "",
            "Habilidades: Python, React, SQL, Git",
            "Proyectos: aplicación web de inventarios con Django (proyecto de aula)",
        ])), save=True)

        # Estudiante sin habilitar (solo puede explorar)
        u2 = self._usuario(f"estudiante2@{dominio}", "Andrés", "Mejía", Rol.ESTUDIANTE, telefono="3017654321")
        PerfilEstudiante.objects.create(usuario=u2, programa=diseno, semestre=4, titular="Estudiante de Diseño Gráfico")

        return {"admin": admin, "oficina": oficina, "estudiante": u1, "estudiante2": u2}

    # ------------------------------------------------------------------ empresas y convocatorias
    def _empresas_y_convocatorias(self, usuarios):
        oficina = usuarios["oficina"]
        medellin = Ciudad.objects.get(nombre="Medellín")
        hoy = timezone.localdate()

        aliada = Empresa.objects.create(
            razon_social="Tech Andina S.A.S.", nit="900123456-7", sector=Sector.objects.get(nombre="Tecnología"),
            tamano=Empresa.Tamano.MEDIANA, ciudad=medellin, sitio_web="https://example.com",
            descripcion="Empresa de desarrollo de software para el sector financiero y logístico.",
            contacto_nombre="Sofía Arango", contacto_email="talento@techandina.example", contacto_telefono="6045550101",
            estado=Empresa.Estado.ALIADA,
        )
        Convenio.objects.create(
            empresa=aliada, numero="CONV-2026-014", fecha_inicio=hoy - timedelta(days=200),
            fecha_fin=hoy + timedelta(days=530), registrado_por=oficina,
        )
        reclutadora = self._usuario("talento@techandina.example", "Sofía", "Arango", Rol.EMPRESA, telefono="6045550101")
        UsuarioEmpresa.objects.create(usuario=reclutadora, empresa=aliada, cargo="Líder de talento humano")

        textil = Empresa.objects.create(
            razon_social="Confecciones Valle de Aburrá S.A.S.", nit="901987654-3",
            sector=Sector.objects.get(nombre="Textil y confección"), tamano=Empresa.Tamano.GRANDE,
            ciudad=Ciudad.objects.get(nombre="Itagüí"), contacto_nombre="Diego Cano",
            contacto_email="practicas@confeccionesvalle.example", estado=Empresa.Estado.ALIADA,
            creada_por_oficina=True,
        )
        Convenio.objects.create(
            empresa=textil, numero="CONV-2025-087", fecha_inicio=hoy - timedelta(days=400),
            fecha_fin=hoy + timedelta(days=60), registrado_por=oficina,
        )

        pendiente = Empresa.objects.create(
            razon_social="Energía Solar del Norte S.A.S.", nit="902555111-0", sector=Sector.objects.get(nombre="Energía"),
            ciudad=Ciudad.objects.get(nombre="Bello"), contacto_nombre="Mario López",
            contacto_email="rrhh@solarnorte.example",
        )
        u_pend = self._usuario("rrhh@solarnorte.example", "Mario", "López", Rol.EMPRESA)
        UsuarioEmpresa.objects.create(usuario=u_pend, empresa=pendiente, cargo="Gerente")

        datos = [
            (aliada, reclutadora, "Practicante de desarrollo web", "PRACTICA", "HIBRIDA", 1_423_500, 2,
             ["Tecnología en Desarrollo de Software", "Ingeniería de Software"], ["Python", "Django", "React", "Git"],
             "Apoyarás al equipo de producto en el desarrollo de aplicaciones web con Django y React.",
             "Desarrollar funcionalidades, escribir pruebas, participar en revisiones de código y ceremonias ágiles."),
            (aliada, reclutadora, "Practicante de análisis de datos", "CONTRATO_APRENDIZAJE", "PRESENCIAL", 1_423_500, 1,
             ["Tecnología en Desarrollo de Software", "Ingeniería Industrial"], ["SQL", "Excel avanzado", "Python"],
             "Construirás reportes y tableros para las áreas de operación.",
             "Limpiar y consolidar datos, construir consultas SQL y tableros de indicadores."),
            (textil, oficina, "Practicante de diseño de modas", "PRACTICA", "PRESENCIAL", None, 3,
             ["Tecnología en Diseño Textil y Producción de Modas", "Diseño Gráfico"], ["Patronaje", "Adobe Illustrator"],
             "Acompañarás al equipo de diseño en el desarrollo de la colección 2027.",
             "Apoyar el patronaje, fichas técnicas y la selección de materiales."),
        ]
        for empresa, autor, titulo, vinculacion, modalidad, apoyo, cupos, programas, habilidades, descripcion, funciones in datos:
            convocatoria = Convocatoria.objects.create(
                empresa=empresa, creada_por=autor, titulo=titulo, descripcion=descripcion, funciones=funciones,
                tipo_vinculacion=vinculacion, modalidad=modalidad, ciudad=empresa.ciudad, apoyo_economico=apoyo,
                cupos=cupos, fecha_inicio=date(2027, 1, 20), duracion_meses=6, fecha_cierre=hoy + timedelta(days=30),
            )
            convocatoria.programas.set(Programa.objects.filter(nombre__in=programas))
            convocatoria.habilidades.set(Habilidad.objects.filter(nombre__in=habilidades))
            publicar(convocatoria, autor)

        # Una convocatoria en revisión para probar la bandeja de la oficina
        en_revision = Convocatoria.objects.create(
            empresa=aliada, creada_por=reclutadora, titulo="Practicante de soporte de infraestructura",
            descripcion="Apoyo al equipo de infraestructura y redes.", funciones="Soporte a usuarios, inventario y monitoreo.",
            tipo_vinculacion="PRACTICA", modalidad="PRESENCIAL", ciudad=medellin, cupos=1,
            fecha_inicio=date(2027, 2, 1), duracion_meses=6, fecha_cierre=hoy + timedelta(days=20),
            estado=Convocatoria.Estado.EN_REVISION,
        )
        en_revision.programas.set(Programa.objects.filter(nombre__in=["Tecnología en Electrónica Industrial", "Tecnología en Desarrollo de Software"]))

    # ------------------------------------------------------------------ muro
    def _muro(self, oficina):
        software = Programa.objects.get(nombre="Tecnología en Desarrollo de Software")
        externa = Publicacion.objects.create(
            autor=oficina, tipo=Publicacion.Tipo.OFERTA_EXTERNA, titulo="Practicantes de desarrollo — convocatoria externa",
            texto="Una empresa del sector salud busca practicantes de software. La postulación se hace en la fuente original.",
            enlace_url="https://example.com/oferta-externa", fuente_externa="Bolsa de empleo de ejemplo",
            para_todos_programas=False,
        )
        externa.programas.set([software])
        Publicacion.objects.create(
            autor=oficina, tipo=Publicacion.Tipo.EVENTO, titulo="Feria de prácticas Pascual Bravo 2026-2",
            texto="Conoce a las empresas aliadas y lleva tu hoja de vida actualizada.",
            fecha_evento=timezone.now() + timedelta(days=12), lugar_evento="Coliseo de la institución",
        )
        Publicacion.objects.create(
            autor=oficina, tipo=Publicacion.Tipo.COMUNICADO, titulo="Inscripciones abiertas al curso de preparación para la práctica",
            texto="Si vas a hacer tu práctica en 2027-1, acércate a la oficina de prácticas para tu habilitación.",
        )
