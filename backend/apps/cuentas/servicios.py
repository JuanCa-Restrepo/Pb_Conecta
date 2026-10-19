"""Registro y verificación de cuentas (M1). Las vistas solo llaman a estas funciones (arquitectura 3.2)."""

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core import signing
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework.exceptions import ValidationError

from apps.empresas.models import Empresa, UsuarioEmpresa
from apps.estudiantes.models import PerfilEstudiante
from apps.notificaciones.servicios import notificar

from .models import ConsentimientoDatos, Rol, Usuario

SAL_VERIFICACION = "pbconecta.verificar-correo"
VIGENCIA_ENLACE_SEGUNDOS = 3 * 24 * 3600


def es_correo_institucional(email):
    """RN-01."""
    return email.lower().endswith("@" + settings.DOMINIO_INSTITUCIONAL.lower())


def _registrar_consentimiento(usuario, ip):
    ConsentimientoDatos.objects.create(usuario=usuario, version_politica=settings.VERSION_POLITICA_DATOS, ip=ip)


@transaction.atomic
def registrar_estudiante(*, email, password, nombres, apellidos, programa, telefono="", documento=None, semestre=None, ip=None):
    usuario = Usuario.objects.create_user(
        email=email, password=password, nombres=nombres, apellidos=apellidos, telefono=telefono,
        rol=Rol.ESTUDIANTE, is_active=False,
    )
    PerfilEstudiante.objects.create(usuario=usuario, programa=programa, documento=documento or None, semestre=semestre)
    _registrar_consentimiento(usuario, ip)
    transaction.on_commit(lambda: enviar_verificacion(usuario))
    return usuario


@transaction.atomic
def registrar_empresa(*, email, password, nombres, apellidos, telefono, cargo, razon_social, nit, sector, ciudad,
                      sitio_web="", descripcion="", ip=None):
    """RF-02: la empresa queda PENDIENTE hasta que la oficina la apruebe y registre el convenio."""
    usuario = Usuario.objects.create_user(
        email=email, password=password, nombres=nombres, apellidos=apellidos, telefono=telefono,
        rol=Rol.EMPRESA, is_active=False,
    )
    empresa = Empresa.objects.create(
        razon_social=razon_social, nit=nit, sector=sector, ciudad=ciudad, sitio_web=sitio_web, descripcion=descripcion,
        contacto_nombre=usuario.nombre_completo, contacto_email=email, contacto_telefono=telefono,
    )
    UsuarioEmpresa.objects.create(usuario=usuario, empresa=empresa, cargo=cargo)
    _registrar_consentimiento(usuario, ip)

    def despues_de_guardar():
        enviar_verificacion(usuario)
        for funcionario in Usuario.objects.filter(rol=Rol.OFICINA, is_active=True):
            notificar(
                funcionario, "EMPRESA_SOLICITUD", "Nueva empresa solicita registro",
                f"{razon_social} (NIT {nit}) solicitó unirse como empresa aliada.", url="/oficina/empresas",
            )

    transaction.on_commit(despues_de_guardar)
    return usuario


def _enviar_enlace(usuario, asunto, mensaje, enlace):
    """Correo con un botón que lleva a una pantalla del frontend (verificación, recuperación de contraseña)."""
    contexto = {"nombre": usuario.nombres, "titulo": asunto, "mensaje": mensaje, "enlace": enlace}
    send_mail(
        subject=f"PB Conecta · {asunto}",
        message=f"Hola {usuario.nombres},\n\n{mensaje}\n{enlace}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[usuario.email],
        html_message=render_to_string("correos/notificacion.html", contexto),
        fail_silently=True,
    )


def enviar_verificacion(usuario):
    token = signing.dumps({"id": usuario.pk}, salt=SAL_VERIFICACION)
    _enviar_enlace(
        usuario, "Confirma tu correo",
        "Para activar tu cuenta en PB Conecta confirma tu correo con el siguiente botón. El enlace vence en 3 días.",
        f"{settings.FRONTEND_URL}/verificar-correo?token={token}",
    )


def verificar_correo(token):
    try:
        datos = signing.loads(token, salt=SAL_VERIFICACION, max_age=VIGENCIA_ENLACE_SEGUNDOS)
    except signing.SignatureExpired:
        raise ValidationError({"token": "El enlace de verificación venció. Solicita uno nuevo."})
    except signing.BadSignature:
        raise ValidationError({"token": "El enlace de verificación no es válido."})

    usuario = Usuario.objects.filter(pk=datos.get("id")).first()
    if usuario is None:
        raise ValidationError({"token": "El enlace de verificación no es válido."})
    if not usuario.is_active:
        usuario.is_active = True
        usuario.email_verificado_en = timezone.now()
        usuario.save(update_fields=["is_active", "email_verificado_en"])
    return usuario


# ------------------------------------------------------------------ contraseña (RF-05)
def solicitar_recuperacion(email):
    """Siempre responde igual, exista o no la cuenta, para no revelar qué correos están registrados."""
    usuario = Usuario.objects.filter(email__iexact=email.strip(), is_active=True).first()
    if usuario is None:
        return
    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    token = default_token_generator.make_token(usuario)
    _enviar_enlace(
        usuario, "Restablece tu contraseña",
        "Recibimos una solicitud para cambiar tu contraseña. Si no fuiste tú, ignora este correo. El enlace vence en 2 horas y sirve una sola vez.",
        f"{settings.FRONTEND_URL}/restablecer-clave?uid={uid}&token={token}",
    )


def _validar_nueva(usuario, nueva):
    try:
        validate_password(nueva, user=usuario)
    except DjangoValidationError as error:
        raise ValidationError({"password": list(error.messages)})


def restablecer_clave(uid, token, nueva):
    try:
        usuario = Usuario.objects.get(pk=force_str(urlsafe_base64_decode(uid)), is_active=True)
    except (Usuario.DoesNotExist, ValueError, TypeError, OverflowError):
        usuario = None
    # El token deja de servir al cambiar la contraseña: es de un solo uso
    if usuario is None or not default_token_generator.check_token(usuario, token):
        raise ValidationError({"token": "El enlace no es válido o ya venció. Solicita uno nuevo."})
    _validar_nueva(usuario, nueva)
    usuario.set_password(nueva)
    usuario.save(update_fields=["password"])
    return usuario


def cambiar_clave(usuario, actual, nueva):
    if not usuario.check_password(actual):
        raise ValidationError({"actual": "La contraseña actual no es correcta."})
    _validar_nueva(usuario, nueva)
    usuario.set_password(nueva)
    usuario.save(update_fields=["password"])
