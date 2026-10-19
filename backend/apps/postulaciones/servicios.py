"""Postulaciones (M6): requisitos para postularse, máquina de estados, entrevistas y bitácora de seguimiento."""

from django.core.files.base import ContentFile
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.comun.errores import ErrorRegla
from apps.convocatorias import afinidad
from apps.convocatorias.models import Convocatoria
from apps.cuentas.models import Rol, Usuario
from apps.estudiantes.models import EstadoEstudiante, PerfilEstudiante
from apps.estudiantes.servicios import faltantes_perfil_minimo
from apps.notificaciones.servicios import notificar

from .models import ESTADOS_ACTIVOS, EntradaSeguimiento, Entrevista, EstadoPostulacion, HistorialEstado, Postulacion

P = EstadoPostulacion
EMPRESA, OFICINA, ESTUDIANTE = Rol.EMPRESA, Rol.OFICINA, Rol.ESTUDIANTE

# RN-13: estado actual → {estado siguiente: roles que pueden hacer el cambio}.
# ENTREVISTA solo se alcanza programando una entrevista y LEGALIZADO con la legalización de la oficina (M7).
TRANSICIONES = {
    P.POSTULADO: {P.EN_REVISION: {EMPRESA, OFICINA}, P.NO_SELECCIONADO: {EMPRESA, OFICINA}},
    P.EN_REVISION: {P.PRESELECCIONADO: {EMPRESA, OFICINA}, P.NO_SELECCIONADO: {EMPRESA, OFICINA}},
    P.PRESELECCIONADO: {P.ENTREVISTA: {EMPRESA}, P.NO_SELECCIONADO: {EMPRESA, OFICINA}},
    P.ENTREVISTA: {P.SELECCIONADO: {EMPRESA}, P.NO_SELECCIONADO: {EMPRESA, OFICINA}},
    P.SELECCIONADO: {P.LEGALIZADO: {OFICINA}},
}
# RF-58: desde la preselección el estudiante ve los datos de contacto de la empresa
ESTADOS_CON_CONTACTO = {P.PRESELECCIONADO, P.ENTREVISTA, P.SELECCIONADO, P.LEGALIZADO}


def _rol(usuario):
    return OFICINA if usuario.rol == Rol.SUPERADMIN else usuario.rol


# ------------------------------------------------------------------ requisitos para postularse (RN-04 a RN-08)
def motivo_perfil(perfil):
    """Lo que impide postularse por el estado o el perfil del estudiante. None si puede."""
    if perfil.estado in (EstadoEstudiante.UBICADO, EstadoEstudiante.EN_PRACTICA):
        return "Ya tienes una práctica legalizada: no puedes postularte a otras convocatorias (RN-08)."
    if perfil.estado != EstadoEstudiante.HABILITADO:
        return "Aún no estás habilitado para prácticas. Acércate a la oficina de prácticas."
    if faltan := faltantes_perfil_minimo(perfil):
        return "Para postularte completa en tu perfil: " + ", ".join(faltan) + "."
    return None


def motivo_convocatoria(perfil, convocatoria, ya_postulado):
    """Lo que impide postularse a esta convocatoria en particular. None si puede."""
    if convocatoria.estado != Convocatoria.Estado.PUBLICADA or convocatoria.fecha_cierre < timezone.localdate():
        return "Esta convocatoria ya no recibe postulaciones."
    if perfil.programa_id not in {p.id for p in convocatoria.programas.all()}:
        return "Esta convocatoria no incluye tu programa (RN-05)."
    if ya_postulado:
        return "Ya te postulaste a esta convocatoria."
    return None


# ------------------------------------------------------------------ notificaciones
def url_postulacion(usuario, postulacion):
    seccion = {ESTUDIANTE: "estudiante", EMPRESA: "empresa"}.get(usuario.rol, "oficina")
    return f"/{seccion}/postulaciones/{postulacion.pk}"


def usuarios_empresa(postulacion):
    return [v.usuario for v in postulacion.convocatoria.empresa.usuarios.select_related("usuario")]


def avisar(destinatarios, tipo, titulo, mensaje, postulacion, correo=True):
    for usuario in destinatarios:
        notificar(usuario, tipo, titulo, mensaje, url=url_postulacion(usuario, postulacion), correo=correo)


# ------------------------------------------------------------------ postular
@transaction.atomic
def postular(perfil, convocatoria, mensaje=""):
    # Se relee y bloquea el perfil: su estado pudo cambiar (habilitación, legalización) después de cargarlo
    perfil = PerfilEstudiante.objects.select_for_update().select_related("usuario").get(pk=perfil.pk)
    ya_postulado = Postulacion.objects.filter(estudiante=perfil, convocatoria=convocatoria).exists()
    if motivo := motivo_perfil(perfil) or motivo_convocatoria(perfil, convocatoria, ya_postulado):
        raise ErrorRegla(motivo)

    postulacion = Postulacion(
        estudiante=perfil, convocatoria=convocatoria, mensaje_presentacion=(mensaje or "").strip(),
        afinidad=afinidad.calcular(perfil, convocatoria)["total"],
    )
    # Copia de la hoja de vida en el momento de postularse: la empresa ve exactamente lo que se le envió
    with perfil.hoja_vida.open("rb") as archivo:
        postulacion.hoja_vida.save("hoja-vida.pdf", ContentFile(archivo.read()), save=False)
    try:
        with transaction.atomic():
            postulacion.save()
    except IntegrityError:  # Doble clic o dos pestañas a la vez (RN-06)
        postulacion.hoja_vida.delete(save=False)
        raise ErrorRegla("Ya te postulaste a esta convocatoria.")
    HistorialEstado.objects.create(postulacion=postulacion, estado_nuevo=P.POSTULADO, usuario=perfil.usuario)

    transaction.on_commit(lambda: avisar(
        usuarios_empresa(postulacion), "POSTULACION_NUEVA", "Nueva postulación",
        f"{perfil.usuario.nombre_completo} se postuló a «{convocatoria.titulo}» (afinidad {postulacion.afinidad} %).",
        postulacion,
    ))
    return postulacion


# ------------------------------------------------------------------ máquina de estados
def estados_siguientes(postulacion, usuario):
    rol = _rol(usuario)
    return [estado for estado, roles in TRANSICIONES.get(postulacion.estado, {}).items() if rol in roles]


def acciones_permitidas(postulacion, usuario):
    rol = _rol(usuario)
    activa = postulacion.estado in ESTADOS_ACTIVOS
    seguimiento = {ESTUDIANTE: ["MENSAJE", "CONTACTO_EXTERNO"], EMPRESA: ["MENSAJE", "CONTACTO_EXTERNO"]}.get(
        rol, ["MENSAJE", "CONTACTO_EXTERNO", "NOTA_INTERNA"]
    )
    oficina_y_seleccionado = rol == OFICINA and postulacion.estado == P.SELECCIONADO
    return {
        # La oficina legaliza con su propio flujo (practicas.py); ENTREVISTA se alcanza programando la entrevista
        "estados": [e for e in estados_siguientes(postulacion, usuario) if e not in (P.ENTREVISTA, P.LEGALIZADO)],
        "programar_entrevista": rol == EMPRESA and postulacion.estado in (P.PRESELECCIONADO, P.ENTREVISTA),
        "retirar": rol == ESTUDIANTE and activa,
        "seguimiento": seguimiento,
        "verificar": oficina_y_seleccionado,  # RF-62a
        "legalizar": oficina_y_seleccionado and ultima_verificacion_cumple(postulacion),  # RN-07
    }


def ultima_verificacion_cumple(postulacion):
    ultima = postulacion.verificaciones.order_by("-creado_en").first()
    return bool(ultima and ultima.resultado == ultima.Resultado.CUMPLE)


def registrar_cambio(postulacion, nuevo, usuario, comentario=""):
    anterior = postulacion.estado
    postulacion.estado = nuevo
    postulacion.save(update_fields=["estado", "motivo_no_seleccion", "actualizado_en"])
    HistorialEstado.objects.create(
        postulacion=postulacion, estado_anterior=anterior, estado_nuevo=nuevo, usuario=usuario, comentario=comentario
    )


@transaction.atomic
def cambiar_estado(postulacion, nuevo, usuario, comentario="", motivo=""):
    postulacion = Postulacion.objects.select_for_update().select_related("convocatoria__empresa", "estudiante__usuario").get(pk=postulacion.pk)
    if nuevo == P.ENTREVISTA:
        raise ErrorRegla("Para pasar a entrevista, programa la entrevista con fecha y lugar.")
    if nuevo not in estados_siguientes(postulacion, usuario):
        raise ErrorRegla(f"No se puede pasar de «{postulacion.get_estado_display()}» a «{P(nuevo).label}».")
    if nuevo == P.NO_SELECCIONADO:
        motivo = (motivo or "").strip()
        if not motivo:
            raise ErrorRegla("El motivo es obligatorio y el estudiante lo verá (RN-11).")
        postulacion.motivo_no_seleccion = motivo
    registrar_cambio(postulacion, nuevo, usuario, (comentario or "").strip())

    estudiante = postulacion.estudiante.usuario
    titulo = postulacion.convocatoria.titulo
    detalle = f" Motivo: {postulacion.motivo_no_seleccion}" if nuevo == P.NO_SELECCIONADO else ""
    transaction.on_commit(lambda: avisar(
        [estudiante], "POSTULACION_ESTADO", "Tu postulación cambió de estado",
        f"«{titulo}»: ahora está {P(nuevo).label.lower()}.{detalle}", postulacion,
    ))
    if nuevo == P.SELECCIONADO:
        transaction.on_commit(lambda: avisar(
            Usuario.objects.filter(rol=Rol.OFICINA, is_active=True), "POSTULANTE_SELECCIONADO", "Postulante seleccionado",
            f"{postulacion.convocatoria.empresa} seleccionó a {estudiante.nombre_completo} para «{titulo}». "
            "Falta verificar requisitos y legalizar la práctica.",
            postulacion,
        ))
    return postulacion


@transaction.atomic
def retirar(postulacion, usuario, comentario=""):
    """RF-52: el estudiante retira su postulación mientras no esté legalizada."""
    postulacion = Postulacion.objects.select_for_update().get(pk=postulacion.pk)
    if postulacion.estudiante.usuario_id != usuario.pk or postulacion.estado not in ESTADOS_ACTIVOS:
        raise ErrorRegla("Esta postulación ya no se puede retirar.")
    registrar_cambio(postulacion, P.RETIRADO, usuario, (comentario or "").strip())
    transaction.on_commit(lambda: avisar(
        usuarios_empresa(postulacion), "POSTULACION_RETIRADA", "Postulación retirada",
        f"{usuario.nombre_completo} retiró su postulación a «{postulacion.convocatoria.titulo}».", postulacion,
    ))
    return postulacion


# ------------------------------------------------------------------ entrevistas (RF-55)
@transaction.atomic
def programar_entrevista(postulacion, usuario, *, fecha_hora, modalidad, lugar_o_enlace, notas=""):
    if not acciones_permitidas(postulacion, usuario)["programar_entrevista"]:
        raise ErrorRegla("Solo se puede programar una entrevista a un postulante preseleccionado.")
    if fecha_hora <= timezone.now():
        raise ErrorRegla("La fecha de la entrevista debe ser futura.")
    entrevista = Entrevista.objects.create(
        postulacion=postulacion, fecha_hora=fecha_hora, modalidad=modalidad, lugar_o_enlace=lugar_o_enlace,
        notas=notas, creada_por=usuario,
    )
    if postulacion.estado == P.PRESELECCIONADO:
        registrar_cambio(postulacion, P.ENTREVISTA, usuario, f"Entrevista programada para el {timezone.localtime(fecha_hora):%d/%m/%Y %H:%M}")

    cuando = timezone.localtime(fecha_hora).strftime("%d/%m/%Y a las %H:%M")
    transaction.on_commit(lambda: avisar(
        [postulacion.estudiante.usuario], "ENTREVISTA", "Entrevista programada",
        f"{postulacion.convocatoria.empresa} te citó a entrevista el {cuando} ({entrevista.get_modalidad_display().lower()}: {lugar_o_enlace}).",
        postulacion,
    ))
    return entrevista


# ------------------------------------------------------------------ bitácora de seguimiento (RF-57, RF-59)
@transaction.atomic
def agregar_seguimiento(postulacion, usuario, *, tipo, texto, canal=None, fecha_contacto=None):
    if tipo not in acciones_permitidas(postulacion, usuario)["seguimiento"]:
        raise ErrorRegla("No puedes registrar este tipo de entrada.")
    if tipo == EntradaSeguimiento.Tipo.CONTACTO_EXTERNO and not (canal and fecha_contacto):
        raise ErrorRegla("Para un contacto por fuera indica el canal y la fecha.")
    if tipo != EntradaSeguimiento.Tipo.CONTACTO_EXTERNO:
        canal, fecha_contacto = None, None
    entrada = EntradaSeguimiento.objects.create(
        postulacion=postulacion, autor=usuario, tipo=tipo, texto=texto.strip(), canal=canal, fecha_contacto=fecha_contacto
    )

    if tipo != EntradaSeguimiento.Tipo.NOTA_INTERNA:  # Las notas internas no se notifican
        participantes = [postulacion.estudiante.usuario, *usuarios_empresa(postulacion)]
        destinatarios = [u for u in participantes if u.pk != usuario.pk]
        transaction.on_commit(lambda: avisar(
            destinatarios, "SEGUIMIENTO", "Nuevo mensaje en una postulación",
            f"{usuario.nombre_completo} escribió en «{postulacion.convocatoria.titulo}»: {entrada.texto[:120]}",
            postulacion, correo=tipo == EntradaSeguimiento.Tipo.MENSAJE,
        ))
    return entrada
