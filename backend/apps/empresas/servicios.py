"""Lógica de negocio de empresas y convenios (M3). Las vistas solo llaman a estas funciones."""

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from apps.catalogos.models import Parametro
from apps.comun.errores import ErrorRegla
from apps.cuentas.models import Rol, Usuario
from apps.notificaciones.servicios import notificar

from .models import Convenio, Empresa

E = Empresa.Estado

# Máquina de estados de la empresa (RN-13)
TRANSICIONES = {
    E.PENDIENTE: {E.ALIADA, E.RECHAZADA},
    E.ALIADA: {E.SUSPENDIDA, E.CONVENIO_VENCIDO},
    E.CONVENIO_VENCIDO: {E.ALIADA, E.SUSPENDIDA},
    E.SUSPENDIDA: {E.ALIADA, E.CONVENIO_VENCIDO},
    E.RECHAZADA: set(),
}


def _cambiar_estado(empresa, nuevo, motivo=""):
    if nuevo not in TRANSICIONES[empresa.estado]:
        raise ErrorRegla(f"No se puede pasar de «{empresa.get_estado_display()}» a «{E(nuevo).label}».")
    empresa.estado = nuevo
    empresa.motivo_estado = motivo
    empresa.save(update_fields=["estado", "motivo_estado"])


def _avisar_empresa(empresa, tipo, titulo, mensaje):
    for vinculo in empresa.usuarios.select_related("usuario"):
        notificar(vinculo.usuario, tipo, titulo, mensaje, url="/empresa")


def _motivo_obligatorio(motivo):
    motivo = (motivo or "").strip()
    if not motivo:
        raise ErrorRegla("El motivo es obligatorio (RN-11).")
    return motivo


def _crear_convenio(empresa, funcionario, numero, fecha_inicio, fecha_fin, documento=None):
    if fecha_fin <= fecha_inicio:
        raise ErrorRegla("La fecha de fin del convenio debe ser posterior a la de inicio.")
    return Convenio.objects.create(
        empresa=empresa, numero=numero, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin,
        documento=documento or "", registrado_por=funcionario,
    )


@transaction.atomic
def aprobar(empresa, funcionario, **convenio):
    """RF-60 + RF-25: aprobar exige registrar un convenio vigente hoy, así la empresa queda aliada."""
    if empresa.estado != E.PENDIENTE:
        raise ErrorRegla("Solo se pueden aprobar empresas pendientes de aprobación.")
    nuevo = _crear_convenio(empresa, funcionario, **convenio)
    hoy = timezone.localdate()
    if not nuevo.fecha_inicio <= hoy <= nuevo.fecha_fin:
        raise ErrorRegla("Para aprobar la empresa, el convenio debe estar vigente hoy.")
    _cambiar_estado(empresa, E.ALIADA)
    transaction.on_commit(lambda: _avisar_empresa(
        empresa, "EMPRESA_APROBADA", "Tu empresa fue aprobada",
        f"{empresa.razon_social} ya es empresa aliada del Pascual Bravo (convenio {nuevo.numero}). Ya puedes publicar convocatorias.",
    ))
    return empresa


@transaction.atomic
def rechazar(empresa, funcionario, motivo):
    motivo = _motivo_obligatorio(motivo)
    if empresa.estado != E.PENDIENTE:
        raise ErrorRegla("Solo se pueden rechazar empresas pendientes de aprobación.")
    _cambiar_estado(empresa, E.RECHAZADA, motivo)
    transaction.on_commit(lambda: _avisar_empresa(
        empresa, "EMPRESA_RECHAZADA", "Solicitud de empresa rechazada", f"La oficina de prácticas rechazó la solicitud. Motivo: {motivo}",
    ))
    return empresa


@transaction.atomic
def suspender(empresa, funcionario, motivo):
    motivo = _motivo_obligatorio(motivo)
    _cambiar_estado(empresa, E.SUSPENDIDA, motivo)
    transaction.on_commit(lambda: _avisar_empresa(
        empresa, "EMPRESA_SUSPENDIDA", "Empresa suspendida", f"La oficina de prácticas suspendió la empresa. Motivo: {motivo}",
    ))
    return empresa


@transaction.atomic
def reactivar(empresa, funcionario):
    if empresa.estado != E.SUSPENDIDA:
        raise ErrorRegla("Solo se pueden reactivar empresas suspendidas.")
    _cambiar_estado(empresa, E.ALIADA if empresa.convenio_vigente() else E.CONVENIO_VENCIDO)
    transaction.on_commit(lambda: _avisar_empresa(
        empresa, "EMPRESA_REACTIVADA", "Empresa reactivada", f"La empresa quedó en estado «{empresa.get_estado_display()}».",
    ))
    return empresa


@transaction.atomic
def registrar_convenio(empresa, funcionario, **convenio):
    """RF-25: renovación o nuevo convenio. Si la empresa tenía el convenio vencido y el nuevo está vigente, vuelve a ser aliada."""
    if empresa.estado in (E.PENDIENTE, E.RECHAZADA):
        raise ErrorRegla("Para una empresa pendiente usa «Aprobar»; una empresa rechazada no puede tener convenios.")
    nuevo = _crear_convenio(empresa, funcionario, **convenio)
    # Se revisa el convenio nuevo directamente: empresa.convenios puede venir precargado (prefetch) sin incluirlo
    if empresa.estado == E.CONVENIO_VENCIDO and nuevo.fecha_inicio <= timezone.localdate() <= nuevo.fecha_fin:
        _cambiar_estado(empresa, E.ALIADA)
        transaction.on_commit(lambda: _avisar_empresa(
            empresa, "CONVENIO_RENOVADO", "Convenio renovado", f"Se registró el convenio {nuevo.numero}. Ya puedes publicar convocatorias.",
        ))
    return nuevo


@transaction.atomic
def crear_por_oficina(funcionario, convenio, **datos):
    """RF-24: la oficina registra una empresa sin cuenta para publicar convocatorias en su nombre."""
    empresa = Empresa.objects.create(creada_por_oficina=True, **datos)
    return aprobar(empresa, funcionario, **convenio)


def revisar_convenios(hoy=None):
    """RF-26 y RN-02: marca empresas con convenio vencido y avisa de los que vencen pronto. Es idempotente."""
    hoy = hoy or timezone.localdate()
    vencidas = 0
    for empresa in Empresa.objects.filter(estado=E.ALIADA).prefetch_related("convenios"):
        if empresa.convenio_vigente(hoy) is None:
            _cambiar_estado(empresa, E.CONVENIO_VENCIDO)
            _avisar_empresa(empresa, "CONVENIO_VENCIDO", "Convenio vencido",
                            "El convenio con el Pascual Bravo venció. Comunícate con la oficina de prácticas para renovarlo.")
            vencidas += 1

    dias_aviso = Parametro.entero("dias_aviso_convenio", 30)
    por_vencer = Convenio.objects.filter(fecha_fin=hoy + timedelta(days=dias_aviso)).select_related("empresa")
    oficina = list(Usuario.objects.filter(rol=Rol.OFICINA, is_active=True))
    for convenio in por_vencer:
        for funcionario in oficina:
            notificar(
                funcionario, "CONVENIO_POR_VENCER", "Convenio próximo a vencer",
                f"El convenio {convenio.numero} con {convenio.empresa} vence el {convenio.fecha_fin:%d/%m/%Y}.",
                url=f"/oficina/empresas/{convenio.empresa_id}",
            )
    return vencidas
