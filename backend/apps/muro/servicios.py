"""Muro de publicaciones (M10): quién publica qué, visibilidad, moderación y participación."""

from django.db import transaction
from django.db.models import Q

from apps.comun.errores import ErrorRegla
from apps.convocatorias.models import Convocatoria
from apps.cuentas.models import Rol, Usuario
from apps.notificaciones.servicios import notificar, notificar_masivo

from .models import Comentario, Publicacion, PublicacionGuardada, Reaccion

T, E = Publicacion.Tipo, Publicacion.Estado
ROLES_OFICINA = (Rol.OFICINA, Rol.SUPERADMIN)

# RF-102: la oficina publica cualquier tipo; las empresas aliadas, noticias y eventos.
# Las publicaciones de tipo CONVOCATORIA las crea el sistema al aprobar una convocatoria (RF-35).
TIPOS_POR_ROL = {
    Rol.OFICINA: {T.OFERTA_EXTERNA, T.EVENTO, T.NOTICIA, T.COMUNICADO},
    Rol.SUPERADMIN: {T.OFERTA_EXTERNA, T.EVENTO, T.NOTICIA, T.COMUNICADO},
    Rol.EMPRESA: {T.EVENTO, T.NOTICIA},
}


def es_oficina(usuario):
    return usuario.rol in ROLES_OFICINA


def tipos_permitidos(usuario):
    if usuario.rol == Rol.EMPRESA:
        vinculo = getattr(usuario, "vinculo_empresa", None)
        if not (vinculo and vinculo.empresa.puede_publicar):
            return set()
    return TIPOS_POR_ROL.get(usuario.rol, set())


def visibles(usuario):
    """Lo que cada rol ve en el muro. La oficina también ve lo oculto para poder moderarlo."""
    estados = [E.PUBLICADA, E.OCULTA] if es_oficina(usuario) else [E.PUBLICADA]
    return Publicacion.objects.filter(estado__in=estados).filter(
        # Una convocatoria en revisión (editada después de publicada) no se muestra hasta que se vuelva a aprobar
        ~Q(tipo=T.CONVOCATORIA) | Q(convocatoria__estado__in=[Convocatoria.Estado.PUBLICADA, Convocatoria.Estado.CERRADA])
    )


def puede_editar(publicacion, usuario):
    return (
        publicacion.tipo != T.CONVOCATORIA
        and publicacion.estado != E.ELIMINADA
        and (publicacion.autor_id == usuario.pk or es_oficina(usuario))
    )


def validar_campos(tipo, datos):
    """RF-101 y RF-104: cada tipo exige sus datos."""
    if tipo == T.OFERTA_EXTERNA and not datos.get("enlace_url"):
        raise ErrorRegla("Una oferta externa necesita el enlace a la fuente original, donde se hace la postulación.")
    if tipo == T.EVENTO and not datos.get("fecha_evento"):
        raise ErrorRegla("Un evento necesita fecha y hora.")
    if not datos.get("para_todos_programas", True) and not datos.get("programas"):
        raise ErrorRegla("Elige al menos un programa destinatario o publícala para todos.")


def _avisar_programas(publicacion):
    """M9: los estudiantes de los programas destinatarios reciben un aviso en la campana (sin correo)."""
    if publicacion.para_todos_programas:
        return
    estudiantes = Usuario.objects.filter(
        rol=Rol.ESTUDIANTE, is_active=True, perfil_estudiante__programa__in=publicacion.programas.all()
    ).exclude(pk=publicacion.autor_id)
    notificar_masivo(
        estudiantes, "MURO_PROGRAMA", "Nueva publicación para tu programa", publicacion.titulo, url="/estudiante/muro"
    )


@transaction.atomic
def crear(usuario, datos, programas):
    tipo = datos["tipo"]
    if tipo not in tipos_permitidos(usuario):
        raise ErrorRegla("No puedes publicar este tipo de contenido en el muro.")
    validar_campos(tipo, {**datos, "programas": programas})
    empresa = usuario.vinculo_empresa.empresa if usuario.rol == Rol.EMPRESA else None
    publicacion = Publicacion.objects.create(autor=usuario, empresa=empresa, **datos)
    publicacion.programas.set([] if publicacion.para_todos_programas else programas)
    transaction.on_commit(lambda: _avisar_programas(publicacion))
    return publicacion


@transaction.atomic
def editar(publicacion, usuario, datos, programas=None):
    if not puede_editar(publicacion, usuario):
        raise ErrorRegla("No puedes editar esta publicación.")
    combinados = {
        "enlace_url": publicacion.enlace_url, "fecha_evento": publicacion.fecha_evento,
        "para_todos_programas": publicacion.para_todos_programas,
        "programas": list(publicacion.programas.all()) if programas is None else programas, **datos,
    }
    validar_campos(publicacion.tipo, combinados)
    for campo, valor in datos.items():
        setattr(publicacion, campo, valor)
    publicacion.save()
    if programas is not None or "para_todos_programas" in datos:
        publicacion.programas.set([] if publicacion.para_todos_programas else combinados["programas"])
    return publicacion


def eliminar(publicacion, usuario):
    """El autor (o la oficina) la retira del muro. Se conserva el registro: borrado lógico."""
    if not puede_editar(publicacion, usuario):
        raise ErrorRegla("No puedes eliminar esta publicación.")
    publicacion.estado = E.ELIMINADA
    publicacion.save(update_fields=["estado"])


# ------------------------------------------------------------------ moderación (RF-105)
@transaction.atomic
def ocultar(publicacion, usuario, motivo):
    motivo = (motivo or "").strip()
    if not motivo:
        raise ErrorRegla("El motivo es obligatorio para ocultar una publicación (RN-11).")
    if publicacion.estado != E.PUBLICADA:
        raise ErrorRegla("Solo se pueden ocultar publicaciones visibles.")
    publicacion.estado = E.OCULTA
    publicacion.motivo_ocultamiento = motivo
    publicacion.save(update_fields=["estado", "motivo_ocultamiento"])
    if publicacion.autor_id != usuario.pk:
        autor = publicacion.autor
        transaction.on_commit(lambda: notificar(
            autor, "MURO_OCULTA", "Tu publicación fue ocultada",
            f"La oficina de prácticas ocultó «{publicacion.titulo}». Motivo: {motivo}", correo=False,
        ))
    return publicacion


def mostrar(publicacion, usuario):
    if publicacion.estado != E.OCULTA:
        raise ErrorRegla("La publicación no está oculta.")
    publicacion.estado = E.PUBLICADA
    publicacion.motivo_ocultamiento = ""
    publicacion.save(update_fields=["estado", "motivo_ocultamiento"])
    return publicacion


def ocultar_comentario(comentario, usuario):
    comentario.oculto = True
    comentario.save(update_fields=["oculto"])


# ------------------------------------------------------------------ participación (RF-106, RF-107)
def alternar_reaccion(publicacion, usuario):
    reaccion, creada = Reaccion.objects.get_or_create(publicacion=publicacion, usuario=usuario)
    if not creada:
        reaccion.delete()
    return creada


def alternar_guardada(publicacion, usuario):
    guardada, creada = PublicacionGuardada.objects.get_or_create(publicacion=publicacion, usuario=usuario)
    if not creada:
        guardada.delete()
    return creada


def comentar(publicacion, usuario, texto):
    texto = (texto or "").strip()
    if not texto:
        raise ErrorRegla("El comentario está vacío.")
    if publicacion.estado != E.PUBLICADA:
        raise ErrorRegla("No se puede comentar esta publicación.")
    return Comentario.objects.create(publicacion=publicacion, autor=usuario, texto=texto)
