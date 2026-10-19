"""Lógica de negocio de las convocatorias (M4): flujo de aprobación, publicación en el muro, búsqueda y cierre automático."""

from django.contrib.postgres.search import SearchVector
from django.db import transaction
from django.db.models import Count, F, Q, Value
from django.utils import timezone

from apps.comun.errores import ErrorRegla
from apps.cuentas.models import Rol, Usuario
from apps.muro.models import Publicacion
from apps.notificaciones.servicios import notificar, notificar_masivo

from .models import Convocatoria

E = Convocatoria.Estado
ROLES_OFICINA = (Rol.OFICINA, Rol.SUPERADMIN)


def es_oficina(usuario):
    return usuario.rol in ROLES_OFICINA


def _creada_por_oficina(convocatoria):
    return convocatoria.creada_por.rol in ROLES_OFICINA


# ------------------------------------------------------------------ permisos de acción (RN-03, RN-13)
def acciones_permitidas(convocatoria, usuario):
    """Acciones que el usuario puede ejecutar sobre la convocatoria. El frontend las usa para mostrar los botones."""
    estado, oficina = convocatoria.estado, es_oficina(usuario)
    acciones = []
    if estado in (E.BORRADOR, E.DEVUELTA, E.PUBLICADA) or (oficina and estado == E.EN_REVISION):
        acciones.append("editar")
    if not oficina and estado in (E.BORRADOR, E.DEVUELTA):
        acciones.append("enviar_revision")
    if oficina and (estado == E.EN_REVISION or (estado == E.BORRADOR and _creada_por_oficina(convocatoria))):
        acciones.append("aprobar")
    if oficina and estado == E.EN_REVISION:
        acciones.append("devolver")
    if estado == E.PUBLICADA:
        acciones.append("cerrar")
    if estado == E.BORRADOR:
        acciones.append("eliminar")
    acciones.append("duplicar")
    return acciones


def _exigir(convocatoria, usuario, accion):
    if accion not in acciones_permitidas(convocatoria, usuario):
        raise ErrorRegla(f"No se puede «{accion.replace('_', ' ')}» una convocatoria en estado «{convocatoria.get_estado_display()}».")


def _verificar_publicable(convocatoria):
    if not convocatoria.empresa.puede_publicar:
        raise ErrorRegla("La empresa no es aliada o no tiene un convenio vigente (RN-02).")
    if convocatoria.fecha_cierre < timezone.localdate():
        raise ErrorRegla("La fecha de cierre ya pasó. Actualízala antes de continuar.")
    if not convocatoria.programas.exists():
        raise ErrorRegla("Selecciona al menos un programa afín (RF-30).")


# ------------------------------------------------------------------ notificaciones
def _avisar_oficina(tipo, titulo, mensaje, convocatoria):
    for funcionario in Usuario.objects.filter(rol=Rol.OFICINA, is_active=True):
        notificar(funcionario, tipo, titulo, mensaje, url=f"/oficina/convocatorias/{convocatoria.pk}")


def _avisar_empresa(tipo, titulo, mensaje, convocatoria):
    for vinculo in convocatoria.empresa.usuarios.select_related("usuario"):
        notificar(vinculo.usuario, tipo, titulo, mensaje, url=f"/empresa/convocatorias/{convocatoria.pk}")


# ------------------------------------------------------------------ búsqueda y publicación
def actualizar_busqueda(convocatoria):
    """Recalcula el vector de búsqueda de texto completo (arquitectura 3.6)."""
    vector = (
        SearchVector("titulo", weight="A", config="spanish")
        + SearchVector("descripcion", "funciones", weight="B", config="spanish")
        + SearchVector(Value(convocatoria.empresa.razon_social), weight="C", config="spanish")
    )
    Convocatoria.objects.filter(pk=convocatoria.pk).update(search_vector=vector)


@transaction.atomic
def publicar(convocatoria, autor):
    """Publica la convocatoria y crea o actualiza su publicación en el muro en la misma transacción (RF-35)."""
    convocatoria.estado = E.PUBLICADA
    convocatoria.publicada_en = timezone.now()
    convocatoria.observacion_revision = ""
    convocatoria.save(update_fields=["estado", "publicada_en", "observacion_revision", "actualizado_en"])
    actualizar_busqueda(convocatoria)

    publicacion, creada = Publicacion.objects.get_or_create(
        convocatoria=convocatoria,
        defaults={
            "autor": autor, "empresa": convocatoria.empresa, "tipo": Publicacion.Tipo.CONVOCATORIA,
            "titulo": convocatoria.titulo, "texto": convocatoria.descripcion, "para_todos_programas": False,
        },
    )
    if not creada:  # Re-publicación después de una edición
        publicacion.titulo, publicacion.texto = convocatoria.titulo, convocatoria.descripcion
        publicacion.save(update_fields=["titulo", "texto"])
    publicacion.programas.set(convocatoria.programas.all())
    if creada:
        transaction.on_commit(lambda: _avisar_nueva_convocatoria(convocatoria))
    return convocatoria


def _avisar_nueva_convocatoria(convocatoria):
    """M9 y RF-23: aviso en la campana a los habilitados de los programas afines y a quienes siguen a la empresa."""
    destinatarios = Usuario.objects.filter(rol=Rol.ESTUDIANTE, is_active=True).filter(
        Q(perfil_estudiante__estado="HABILITADO", perfil_estudiante__programa__in=convocatoria.programas.all())
        | Q(perfil_estudiante__empresaseguida__empresa=convocatoria.empresa)
    ).distinct()
    notificar_masivo(
        destinatarios, "CONVOCATORIA_NUEVA", f"Nueva convocatoria: {convocatoria.titulo}",
        f"{convocatoria.empresa} publicó una convocatoria. Revisa si es afín a tu perfil.",
        url=f"/estudiante/convocatorias/{convocatoria.pk}",
    )


# ------------------------------------------------------------------ flujo de aprobación
@transaction.atomic
def enviar_revision(convocatoria, usuario):
    _exigir(convocatoria, usuario, "enviar_revision")
    _verificar_publicable(convocatoria)
    convocatoria.estado = E.EN_REVISION
    convocatoria.save(update_fields=["estado", "actualizado_en"])
    transaction.on_commit(lambda: _avisar_oficina(
        "CONVOCATORIA_REVISION", "Convocatoria por revisar",
        f"{convocatoria.empresa} envió «{convocatoria.titulo}» a revisión.", convocatoria,
    ))
    return convocatoria


@transaction.atomic
def aprobar(convocatoria, usuario):
    _exigir(convocatoria, usuario, "aprobar")
    _verificar_publicable(convocatoria)
    publicar(convocatoria, usuario)
    if not _creada_por_oficina(convocatoria):
        transaction.on_commit(lambda: _avisar_empresa(
            "CONVOCATORIA_PUBLICADA", "Convocatoria publicada",
            f"La oficina de prácticas aprobó «{convocatoria.titulo}». Ya es visible para los estudiantes.", convocatoria,
        ))
    return convocatoria


@transaction.atomic
def devolver(convocatoria, usuario, observacion):
    observacion = (observacion or "").strip()
    if not observacion:
        raise ErrorRegla("Escribe las observaciones para la empresa (RN-11).")
    _exigir(convocatoria, usuario, "devolver")
    convocatoria.estado = E.DEVUELTA
    convocatoria.observacion_revision = observacion
    convocatoria.save(update_fields=["estado", "observacion_revision", "actualizado_en"])
    transaction.on_commit(lambda: _avisar_empresa(
        "CONVOCATORIA_DEVUELTA", "Convocatoria devuelta con observaciones",
        f"«{convocatoria.titulo}»: {observacion}", convocatoria,
    ))
    return convocatoria


@transaction.atomic
def cerrar(convocatoria, usuario):
    _exigir(convocatoria, usuario, "cerrar")
    convocatoria.estado = E.CERRADA
    convocatoria.motivo_cierre = Convocatoria.MotivoCierre.MANUAL
    convocatoria.save(update_fields=["estado", "motivo_cierre", "actualizado_en"])
    return convocatoria


def eliminar(convocatoria, usuario):
    _exigir(convocatoria, usuario, "eliminar")
    convocatoria.delete()


@transaction.atomic
def duplicar(convocatoria, usuario):
    """RF-33: crea un borrador con los mismos datos."""
    programas, habilidades = list(convocatoria.programas.all()), list(convocatoria.habilidades.all())
    copia = Convocatoria.objects.get(pk=convocatoria.pk)
    copia.pk = None
    copia.titulo = f"{convocatoria.titulo} (copia)"[:150]
    copia.creada_por = usuario
    copia.estado = E.BORRADOR
    copia.observacion_revision = ""
    copia.motivo_cierre = None
    copia.publicada_en = None
    copia.search_vector = None
    copia.save()
    copia.programas.set(programas)
    copia.habilidades.set(habilidades)
    return copia


@transaction.atomic
def despues_de_editar(convocatoria, usuario, estado_anterior):
    """RF-33: si la empresa edita una convocatoria publicada, vuelve a revisión; si la edita la oficina, se republica."""
    if estado_anterior != E.PUBLICADA:
        return convocatoria
    if es_oficina(usuario):
        publicar(convocatoria, usuario)
        return convocatoria
    convocatoria.estado = E.EN_REVISION
    convocatoria.save(update_fields=["estado", "actualizado_en"])
    transaction.on_commit(lambda: _avisar_oficina(
        "CONVOCATORIA_REVISION", "Convocatoria editada por revisar",
        f"{convocatoria.empresa} editó «{convocatoria.titulo}», que estaba publicada. Requiere una nueva revisión.", convocatoria,
    ))
    return convocatoria


# ------------------------------------------------------------------ tareas programadas
def cerrar_vencidas(hoy=None):
    """RN-09: cierra por fecha de cierre o por cupos legalizados. Es idempotente."""
    hoy = hoy or timezone.localdate()
    publicadas = Convocatoria.objects.filter(estado=E.PUBLICADA).select_related("empresa")

    por_fecha = list(publicadas.filter(fecha_cierre__lt=hoy))
    por_cupos = list(
        publicadas.filter(fecha_cierre__gte=hoy)
        .annotate(legalizadas=Count("postulaciones", filter=Q(postulaciones__estado="LEGALIZADO")))
        .filter(legalizadas__gte=F("cupos"))
    )

    cerradas = 0
    for convocatoria, motivo in [(c, "FECHA") for c in por_fecha] + [(c, "CUPOS") for c in por_cupos]:
        convocatoria.estado = E.CERRADA
        convocatoria.motivo_cierre = motivo
        convocatoria.save(update_fields=["estado", "motivo_cierre", "actualizado_en"])
        _avisar_empresa(
            "CONVOCATORIA_CERRADA", "Convocatoria cerrada",
            f"«{convocatoria.titulo}» se cerró automáticamente ({convocatoria.get_motivo_cierre_display().lower()}).",
            convocatoria,
        )
        cerradas += 1
    return cerradas
