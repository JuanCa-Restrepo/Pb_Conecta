"""M7: verificación de requisitos, legalización de la práctica y su ciclo de vida (RF-62a, RF-64, RF-65, RN-07 a RN-09)."""

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.comun.errores import ErrorRegla
from apps.convocatorias.models import Convocatoria
from apps.cuentas.models import Rol
from apps.estudiantes.models import EstadoEstudiante, PerfilEstudiante

from .models import ESTADOS_ACTIVOS, EstadoPostulacion, Postulacion, Practica, VerificacionRequisitos
from .servicios import acciones_permitidas, avisar, registrar_cambio, usuarios_empresa

P = EstadoPostulacion
EP = Practica.Estado


def _bloquear(postulacion):
    return Postulacion.objects.select_for_update().select_related(
        "convocatoria__empresa", "estudiante__usuario"
    ).get(pk=postulacion.pk)


# ------------------------------------------------------------------ verificación (RF-62a)
@transaction.atomic
def verificar(postulacion, funcionario, resultado, observacion=""):
    """La oficina registra que habló con el estudiante seleccionado y revisó sus requisitos."""
    postulacion = _bloquear(postulacion)
    if not acciones_permitidas(postulacion, funcionario)["verificar"]:
        raise ErrorRegla("Solo se verifican los requisitos de un postulante seleccionado.")
    observacion = (observacion or "").strip()
    if resultado == VerificacionRequisitos.Resultado.NO_CUMPLE and not observacion:
        raise ErrorRegla("Indica qué requisito no cumple (RN-11).")

    verificacion = VerificacionRequisitos.objects.create(
        postulacion=postulacion, funcionario=funcionario, resultado=resultado, observacion=observacion
    )
    if resultado == VerificacionRequisitos.Resultado.NO_CUMPLE:
        transaction.on_commit(lambda: avisar(
            [postulacion.estudiante.usuario], "VERIFICACION_NO_CUMPLE", "Requisitos pendientes para tu práctica",
            f"La oficina de prácticas revisó tus requisitos para «{postulacion.convocatoria.titulo}»: {observacion}",
            postulacion,
        ))
    return verificacion


# ------------------------------------------------------------------ legalización (RF-64)
@transaction.atomic
def legalizar(postulacion, funcionario, *, fecha_inicio, fecha_fin, tipo_vinculacion, asesor_nombre,
              tutor_empresa_nombre, tutor_empresa_email="", documento_soporte=None):
    postulacion = _bloquear(postulacion)
    if not acciones_permitidas(postulacion, funcionario)["legalizar"]:
        raise ErrorRegla("Para legalizar, el postulante debe estar seleccionado y con la verificación de requisitos en «Cumple» (RN-07).")
    if fecha_fin <= fecha_inicio:
        raise ErrorRegla("La fecha de fin debe ser posterior a la de inicio.")

    hoy = timezone.localdate()
    perfil = PerfilEstudiante.objects.select_for_update().get(pk=postulacion.estudiante_id)
    en_curso = fecha_inicio <= hoy
    try:
        with transaction.atomic():
            practica = Practica.objects.create(
                postulacion=postulacion, estudiante=perfil, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin,
                tipo_vinculacion=tipo_vinculacion, asesor_nombre=asesor_nombre.strip(),
                tutor_empresa_nombre=tutor_empresa_nombre.strip(), tutor_empresa_email=tutor_empresa_email,
                documento_soporte=documento_soporte or "", legalizada_por=funcionario,
                estado=EP.EN_CURSO if en_curso else EP.LEGALIZADA,
            )
    except IntegrityError:  # Índice único parcial: una sola práctica activa por estudiante (RN-08)
        raise ErrorRegla("El estudiante ya tiene una práctica activa.")

    registrar_cambio(postulacion, P.LEGALIZADO, funcionario, f"Práctica del {fecha_inicio:%d/%m/%Y} al {fecha_fin:%d/%m/%Y}")
    perfil.estado = EstadoEstudiante.EN_PRACTICA if en_curso else EstadoEstudiante.UBICADO
    perfil.save(update_fields=["estado", "actualizado_en"])

    cerradas = _cerrar_otras_postulaciones(perfil, postulacion, funcionario)
    _cerrar_convocatoria_si_cupos_completos(postulacion.convocatoria)

    convocatoria = postulacion.convocatoria
    transaction.on_commit(lambda: avisar(
        [perfil.usuario, *usuarios_empresa(postulacion)], "PRACTICA_LEGALIZADA", "Práctica legalizada",
        f"La práctica de {perfil.usuario.nombre_completo} en {convocatoria.empresa} («{convocatoria.titulo}») quedó legalizada: "
        f"del {fecha_inicio:%d/%m/%Y} al {fecha_fin:%d/%m/%Y}.",
        postulacion,
    ))
    for otra in cerradas:
        transaction.on_commit(lambda otra=otra: avisar(
            usuarios_empresa(otra), "POSTULACION_CERRADA", "Postulación cerrada",
            f"{perfil.usuario.nombre_completo} ya legalizó su práctica en otra empresa; su postulación a «{otra.convocatoria.titulo}» se cerró.",
            otra, correo=False,
        ))
    return practica


def _cerrar_otras_postulaciones(perfil, legalizada, funcionario):
    """RN-08: las demás postulaciones activas del estudiante pasan a «Cerrado por sistema»."""
    otras = list(
        Postulacion.objects.select_for_update().select_related("convocatoria__empresa")
        .filter(estudiante=perfil, estado__in=ESTADOS_ACTIVOS).exclude(pk=legalizada.pk)
    )
    for otra in otras:
        registrar_cambio(otra, P.CERRADO_SISTEMA, None, "El estudiante legalizó su práctica en otra convocatoria.")
    return otras


def _cerrar_convocatoria_si_cupos_completos(convocatoria):
    """RN-09: al legalizar el último cupo, la convocatoria se cierra en ese momento (sin esperar al scheduler)."""
    legalizadas = convocatoria.postulaciones.filter(estado=P.LEGALIZADO).count()
    if convocatoria.estado == Convocatoria.Estado.PUBLICADA and legalizadas >= convocatoria.cupos:
        convocatoria.estado = Convocatoria.Estado.CERRADA
        convocatoria.motivo_cierre = Convocatoria.MotivoCierre.CUPOS
        convocatoria.save(update_fields=["estado", "motivo_cierre", "actualizado_en"])


# ------------------------------------------------------------------ ciclo de vida de la práctica (RF-65)
def _avisar_practica(practica, tipo, titulo, mensaje):
    postulacion = practica.postulacion
    avisar([practica.estudiante.usuario, *usuarios_empresa(postulacion)], tipo, titulo, mensaje, postulacion)


@transaction.atomic
def finalizar(practica, funcionario, observacion):
    practica = Practica.objects.select_for_update().select_related("estudiante__usuario", "postulacion__convocatoria__empresa").get(pk=practica.pk)
    observacion = (observacion or "").strip()
    if not observacion:
        raise ErrorRegla("Escribe una observación de cierre.")
    if practica.estado not in (EP.LEGALIZADA, EP.EN_CURSO):
        raise ErrorRegla(f"La práctica ya está «{practica.get_estado_display()}».")
    practica.estado = EP.FINALIZADA
    practica.observacion_cierre = observacion
    practica.finalizada_en = timezone.now()
    practica.save(update_fields=["estado", "observacion_cierre", "finalizada_en"])
    PerfilEstudiante.objects.filter(pk=practica.estudiante_id).update(estado=EstadoEstudiante.PRACTICA_FINALIZADA)
    transaction.on_commit(lambda: _avisar_practica(
        practica, "PRACTICA_FINALIZADA", "Práctica finalizada", "La oficina de prácticas registró el cierre de la práctica. ¡Felicitaciones!",
    ))
    return practica


@transaction.atomic
def cancelar(practica, funcionario, motivo):
    """La práctica no se realizó o se interrumpió: el estudiante vuelve a quedar habilitado para buscar otra (RN-08)."""
    practica = Practica.objects.select_for_update().select_related("estudiante__usuario", "postulacion__convocatoria__empresa").get(pk=practica.pk)
    motivo = (motivo or "").strip()
    if not motivo:
        raise ErrorRegla("El motivo es obligatorio para cancelar (RN-11).")
    if practica.estado not in (EP.LEGALIZADA, EP.EN_CURSO):
        raise ErrorRegla(f"La práctica ya está «{practica.get_estado_display()}».")
    practica.estado = EP.CANCELADA
    practica.observacion_cierre = motivo
    practica.finalizada_en = timezone.now()
    practica.save(update_fields=["estado", "observacion_cierre", "finalizada_en"])
    PerfilEstudiante.objects.filter(pk=practica.estudiante_id).update(estado=EstadoEstudiante.HABILITADO)
    transaction.on_commit(lambda: _avisar_practica(
        practica, "PRACTICA_CANCELADA", "Práctica cancelada", f"La oficina de prácticas canceló la práctica. Motivo: {motivo}",
    ))
    return practica


def iniciar_practicas(hoy=None):
    """Tarea diaria: las prácticas legalizadas pasan a «En curso» al llegar su fecha de inicio. Es idempotente."""
    hoy = hoy or timezone.localdate()
    por_iniciar = Practica.objects.filter(estado=EP.LEGALIZADA, fecha_inicio__lte=hoy)
    estudiantes = list(por_iniciar.values_list("estudiante_id", flat=True))
    iniciadas = por_iniciar.update(estado=EP.EN_CURSO)
    PerfilEstudiante.objects.filter(pk__in=estudiantes, estado=EstadoEstudiante.UBICADO).update(estado=EstadoEstudiante.EN_PRACTICA)
    return iniciadas


def practicas_de(usuario):
    """Prácticas visibles para cada rol (RNF-05)."""
    consulta = Practica.objects.select_related(
        "estudiante__usuario", "estudiante__programa", "postulacion__convocatoria__empresa", "legalizada_por"
    )
    if usuario.rol == Rol.ESTUDIANTE:
        return consulta.filter(estudiante__usuario=usuario)
    if usuario.rol == Rol.EMPRESA:
        vinculo = getattr(usuario, "vinculo_empresa", None)
        return consulta.filter(postulacion__convocatoria__empresa=vinculo.empresa) if vinculo else consulta.none()
    return consulta

