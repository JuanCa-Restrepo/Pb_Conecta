"""Fábricas de datos para las pruebas automatizadas."""

from datetime import timedelta
from itertools import count

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from apps.catalogos.models import Ciudad, Facultad, Habilidad, PeriodoAcademico, Programa, Sector
from apps.convocatorias.models import Convocatoria
from apps.convocatorias.servicios import publicar
from apps.cuentas.models import Rol, Usuario
from apps.empresas.models import Convenio, Empresa, UsuarioEmpresa
from apps.estudiantes.models import EstudianteHabilidad, PerfilEstudiante

CLAVE = "UnaClaveSegura#1"
_secuencia = count(1)


def usuario(rol, **extra):
    n = next(_secuencia)
    dominio = "pascualbravo.edu.co" if rol in (Rol.ESTUDIANTE, Rol.OFICINA) else "empresa.example"
    return Usuario.objects.create_user(
        email=f"u{n}@{dominio}", password=CLAVE, nombres=f"Nombre{n}", apellidos="Prueba", rol=rol, is_active=True, **extra
    )


def catalogos():
    facultad, _ = Facultad.objects.get_or_create(nombre="Ingeniería")
    software, _ = Programa.objects.get_or_create(nombre="Software", nivel="TECNOLOGICO", defaults={"facultad": facultad})
    diseno, _ = Programa.objects.get_or_create(nombre="Diseño", nivel="PROFESIONAL", defaults={"facultad": facultad})
    sector, _ = Sector.objects.get_or_create(nombre="Tecnología")
    ciudad, _ = Ciudad.objects.get_or_create(nombre="Medellín", departamento="Antioquia")
    hoy = timezone.localdate()
    periodo, _ = PeriodoAcademico.objects.get_or_create(
        codigo="2026-2", defaults={"fecha_inicio": hoy - timedelta(days=60), "fecha_fin": hoy + timedelta(days=90), "vigente": True}
    )
    return {"software": software, "diseno": diseno, "sector": sector, "ciudad": ciudad, "periodo": periodo}


def empresa(estado=Empresa.Estado.ALIADA, convenio_vigente=True, **extra):
    """Empresa con un usuario reclutador. Si es aliada, se le crea un convenio (vigente o vencido)."""
    datos = catalogos()
    n = next(_secuencia)
    nueva = Empresa.objects.create(
        razon_social=f"Empresa {n}", nit=f"90000{n:04d}-1", sector=datos["sector"], ciudad=datos["ciudad"],
        contacto_nombre="Contacto", contacto_email=f"contacto{n}@empresa.example", estado=estado, **extra,
    )
    reclutador = usuario(Rol.EMPRESA)
    UsuarioEmpresa.objects.create(usuario=reclutador, empresa=nueva)
    if estado != Empresa.Estado.PENDIENTE:
        hoy = timezone.localdate()
        inicio, fin = (hoy - timedelta(days=30), hoy + timedelta(days=300)) if convenio_vigente else (hoy - timedelta(days=400), hoy - timedelta(days=1))
        Convenio.objects.create(empresa=nueva, numero=f"CONV-{n}", fecha_inicio=inicio, fecha_fin=fin, registrado_por=reclutador)
    return nueva, reclutador


def estudiante(programa=None, **extra):
    datos = catalogos()
    cuenta = usuario(Rol.ESTUDIANTE)
    return PerfilEstudiante.objects.create(usuario=cuenta, programa=programa or datos["software"], **extra)


PDF_MINIMO = b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


def pdf(nombre="hoja-vida.pdf"):
    return SimpleUploadedFile(nombre, PDF_MINIMO, content_type="application/pdf")


def estudiante_listo(programa=None, habilidades=("Python",), **extra):
    """Estudiante habilitado con el perfil mínimo completo (RN-04): puede postularse."""
    extra.setdefault("estado", "HABILITADO")
    perfil = estudiante(programa=programa, semestre=6, **extra)
    perfil.usuario.telefono = "3000000000"
    perfil.usuario.save(update_fields=["telefono"])
    for nombre in habilidades:
        habilidad, _ = Habilidad.objects.get_or_create(nombre=nombre)
        EstudianteHabilidad.objects.create(estudiante=perfil, habilidad=habilidad, nivel="INTERMEDIO")
    perfil.hoja_vida.save("hv.pdf", ContentFile(PDF_MINIMO), save=True)
    return perfil


def convocatoria(empresa_, programas, habilidades=(), **extra):
    """Convocatoria publicada de la empresa para los programas dados."""
    datos = catalogos()
    hoy = timezone.localdate()
    autor = empresa_.usuarios.first().usuario
    campos = {
        "titulo": "Practicante", "descripcion": "Desarrollo de software", "funciones": "Programar",
        "modalidad": "PRESENCIAL", "ciudad": datos["ciudad"], "tipo_vinculacion": "PRACTICA", "cupos": 2,
        "fecha_inicio": hoy + timedelta(days=60), "fecha_cierre": hoy + timedelta(days=20), **extra,
    }
    nueva = Convocatoria.objects.create(empresa=empresa_, creada_por=autor, **campos)
    nueva.programas.set(programas)
    nueva.habilidades.set([Habilidad.objects.get_or_create(nombre=n)[0] for n in habilidades])
    return publicar(nueva, autor)
