"""Punto único de envío de notificaciones (RF-90, RF-91 · arquitectura 3.9)."""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import Notificacion

log = logging.getLogger(__name__)


def notificar(usuario, tipo, titulo, mensaje, url="", correo=True):
    """Crea la notificación de la campana y, si se pide, envía el correo. Un fallo de correo no rompe la operación."""
    notificacion = Notificacion.objects.create(
        usuario=usuario, tipo=tipo, titulo=titulo, mensaje=mensaje, url_destino=url
    )
    if correo:
        enlace = f"{settings.FRONTEND_URL}{url}" if url else settings.FRONTEND_URL
        contexto = {"nombre": usuario.nombres, "titulo": titulo, "mensaje": mensaje, "enlace": enlace}
        try:
            send_mail(
                subject=f"PB Conecta · {titulo}",
                message=f"Hola {usuario.nombres},\n\n{mensaje}\n\n{enlace}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[usuario.email],
                html_message=render_to_string("correos/notificacion.html", contexto),
            )
            notificacion.enviada_correo = True
            notificacion.save(update_fields=["enviada_correo"])
        except Exception:  # noqa: BLE001 — el correo es secundario, la notificación ya quedó guardada
            log.exception("No se pudo enviar el correo de la notificación %s", notificacion.pk)
    return notificacion


def notificar_masivo(usuarios, tipo, titulo, mensaje, url=""):
    """Avisos solo en la campana para muchos destinatarios a la vez (sin correo, para no saturar). Devuelve cuántos."""
    avisos = [Notificacion(usuario=u, tipo=tipo, titulo=titulo, mensaje=mensaje, url_destino=url) for u in usuarios]
    Notificacion.objects.bulk_create(avisos, batch_size=500)
    return len(avisos)
