"""Validación de archivos subidos y entrega de archivos protegidos (RNF-06 · arquitectura 3.5)."""

import mimetypes
import os

from django.conf import settings
from django.http import Http404, HttpResponse
from rest_framework import serializers


def validar_pdf(archivo):
    """Acepta solo PDF reales (extensión + firma %PDF) dentro del tamaño máximo."""
    if os.path.splitext(archivo.name)[1].lower() != ".pdf":
        raise serializers.ValidationError("El archivo debe ser un PDF.")
    if archivo.size > settings.MAX_ARCHIVO_MB * 1024 * 1024:
        raise serializers.ValidationError(f"El archivo supera el máximo de {settings.MAX_ARCHIVO_MB} MB.")
    inicio = archivo.read(5)
    archivo.seek(0)
    if inicio != b"%PDF-":
        raise serializers.ValidationError("El archivo no es un PDF válido.")
    return archivo


def respuesta_protegida(archivo, nombre_descarga):
    """Pide a Nginx que entregue el archivo desde /protegido/ después de que la vista verificó los permisos."""
    if not archivo:
        raise Http404("No hay archivo")
    respuesta = HttpResponse()
    respuesta["Content-Type"] = mimetypes.guess_type(archivo.name)[0] or "application/octet-stream"
    respuesta["Content-Disposition"] = f'inline; filename="{nombre_descarga}"'
    respuesta["X-Accel-Redirect"] = "/" + archivo.name  # p. ej. /protegido/convenios/<uuid>.pdf
    return respuesta


EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".webp"}


def validar_imagen(archivo):
    """Imágenes públicas (logos, fotos del muro). Pillow ya verificó que es una imagen real (ImageField)."""
    if os.path.splitext(archivo.name)[1].lower() not in EXTENSIONES_IMAGEN:
        raise serializers.ValidationError("La imagen debe ser JPG, PNG o WEBP.")
    if archivo.size > settings.MAX_ARCHIVO_MB * 1024 * 1024:
        raise serializers.ValidationError(f"La imagen supera el máximo de {settings.MAX_ARCHIVO_MB} MB.")
    return archivo
