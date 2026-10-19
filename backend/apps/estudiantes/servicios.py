"""Habilitación de estudiantes (RF-62, RF-70, RN-15) y perfil del estudiante (M2)."""

from django.db import transaction

from apps.catalogos.models import Habilidad, PeriodoAcademico
from apps.comun.errores import ErrorRegla
from apps.notificaciones.servicios import notificar

from .models import EstadoEstudiante, EstudianteHabilidad, Habilitacion, PerfilEstudiante


def _periodo_vigente():
    periodo = PeriodoAcademico.actual()
    if periodo is None:
        raise ErrorRegla("No hay un periodo académico vigente. El superadministrador debe marcar uno como vigente.")
    return periodo


@transaction.atomic
def habilitar(perfil, funcionario, observacion=""):
    perfil = PerfilEstudiante.objects.select_for_update().get(pk=perfil.pk)
    if perfil.estado != EstadoEstudiante.NO_HABILITADO:
        raise ErrorRegla(f"{perfil} ya está en estado «{perfil.get_estado_display()}».")
    periodo = _periodo_vigente()
    Habilitacion.objects.create(
        estudiante=perfil, periodo=periodo, accion=Habilitacion.Accion.HABILITADO, funcionario=funcionario,
        observacion=(observacion or "").strip(),
    )
    perfil.estado = EstadoEstudiante.HABILITADO
    perfil.save(update_fields=["estado", "actualizado_en"])
    transaction.on_commit(lambda: notificar(
        perfil.usuario, "HABILITACION", "Ya estás habilitado para prácticas",
        f"La oficina de prácticas te habilitó para el periodo {periodo}. Ya puedes postularte a las convocatorias de tu programa.",
        url="/estudiante",
    ))
    return perfil


@transaction.atomic
def deshabilitar(perfil, funcionario, motivo):
    """RN-15: sus postulaciones activas no se cierran, pero no puede crear nuevas."""
    motivo = (motivo or "").strip()
    if not motivo:
        raise ErrorRegla("El motivo es obligatorio para deshabilitar (RN-11).")
    perfil = PerfilEstudiante.objects.select_for_update().get(pk=perfil.pk)
    if perfil.estado != EstadoEstudiante.HABILITADO:
        raise ErrorRegla(f"Solo se puede deshabilitar a un estudiante habilitado; {perfil} está «{perfil.get_estado_display()}».")
    Habilitacion.objects.create(
        estudiante=perfil, periodo=_periodo_vigente(), accion=Habilitacion.Accion.DESHABILITADO, funcionario=funcionario,
        observacion=motivo,
    )
    perfil.estado = EstadoEstudiante.NO_HABILITADO
    perfil.save(update_fields=["estado", "actualizado_en"])
    transaction.on_commit(lambda: notificar(
        perfil.usuario, "DESHABILITACION", "Tu habilitación para prácticas fue retirada",
        f"La oficina de prácticas retiró tu habilitación. Motivo: {motivo}", url="/estudiante",
    ))
    return perfil


def habilitar_varios(ids, funcionario, observacion=""):
    """RF-70: habilita a cada estudiante por separado; los que no se pueden habilitar se informan sin detener a los demás."""
    habilitados, omitidos = [], []
    for perfil in PerfilEstudiante.objects.filter(pk__in=ids).select_related("usuario"):
        try:
            habilitar(perfil, funcionario, observacion)
            habilitados.append(perfil.pk)
        except ErrorRegla as error:
            omitidos.append({"id": perfil.pk, "nombre": str(perfil), "motivo": str(error.detail["detail"][0])})
    return {"habilitados": habilitados, "omitidos": omitidos}


# ------------------------------------------------------------------ perfil del estudiante (M2)
def completitud(perfil):
    """RF-15: porcentaje del perfil y lo que falta. El orden es el de prioridad para el estudiante."""
    usuario = perfil.usuario
    criterios = [
        ("hoja_vida", "Sube tu hoja de vida en PDF", bool(perfil.hoja_vida)),
        ("habilidades", "Agrega al menos una habilidad", perfil.habilidades.exists()),
        ("telefono", "Registra tu teléfono", bool(usuario.telefono)),
        ("semestre", "Indica tu semestre", perfil.semestre is not None),
        ("titular", "Escribe un titular profesional", bool(perfil.titular.strip())),
        ("acerca_de", "Cuéntale a las empresas sobre ti", bool(perfil.acerca_de.strip())),
        ("disponibilidad", "Indica tu disponibilidad y modalidad preferida", bool(perfil.fecha_disponible and perfil.modalidad_preferida)),
        ("trayectoria", "Agrega una experiencia o un proyecto", perfil.experiencias.exists() or perfil.proyectos.exists()),
        ("enlaces", "Agrega un enlace (LinkedIn, GitHub o portafolio)", perfil.enlaces.exists()),
    ]
    cumplidos = sum(1 for _, _, ok in criterios if ok)
    return {
        "porcentaje": round(100 * cumplidos / len(criterios)),
        "faltantes": [{"clave": clave, "texto": texto} for clave, texto, ok in criterios if not ok],
    }


def faltantes_perfil_minimo(perfil):
    """RN-04: lo mínimo para postularse (además de estar habilitado)."""
    faltan = []
    if not perfil.hoja_vida:
        faltan.append("tu hoja de vida")
    if perfil.semestre is None:
        faltan.append("tu semestre")
    if not perfil.usuario.telefono:
        faltan.append("tu teléfono")
    if not perfil.habilidades.exists():
        faltan.append("al menos una habilidad")
    return faltan


@transaction.atomic
def reemplazar_habilidades(perfil, items):
    """RF-11: cada item trae `habilidad` (id del catálogo) o `nombre` (nueva, creada por el estudiante) y `nivel`."""
    elegidas = {}
    for item in items:
        if item.get("habilidad"):
            habilidad = item["habilidad"]
        else:
            nombre = item["nombre"].strip()
            habilidad = Habilidad.objects.filter(nombre__iexact=nombre).first() or Habilidad.objects.create(
                nombre=nombre, creada_por_usuario=True
            )
        elegidas[habilidad.pk] = (habilidad, item.get("nivel") or EstudianteHabilidad.Nivel.BASICO)

    EstudianteHabilidad.objects.filter(estudiante=perfil).delete()
    EstudianteHabilidad.objects.bulk_create(
        EstudianteHabilidad(estudiante=perfil, habilidad=habilidad, nivel=nivel) for habilidad, nivel in elegidas.values()
    )
    perfil.save(update_fields=["actualizado_en"])


def guardar_hoja_vida(perfil, archivo):
    """Reemplaza la hoja de vida. Las postulaciones conservan su propia copia, así que el archivo anterior se puede borrar."""
    anterior = perfil.hoja_vida.name if perfil.hoja_vida else None
    perfil.hoja_vida.save("hoja-vida.pdf", archivo, save=True)
    if anterior:
        perfil.hoja_vida.storage.delete(anterior)


def borrar_hoja_vida(perfil):
    if perfil.hoja_vida:
        perfil.hoja_vida.delete(save=True)
