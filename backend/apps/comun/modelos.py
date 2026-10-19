"""Utilidades compartidas por los modelos de todas las apps."""

import os
import uuid

from django.db import models
from django.utils.deconstruct import deconstructible


def ck_opciones(tabla, campo, opciones, nulo=False):
    """CHECK que limita un campo a los valores de un TextChoices (ver docs/03-modelo-datos.md, sección 1)."""
    condicion = models.Q(**{f"{campo}__in": opciones.values})
    if nulo:
        condicion |= models.Q(**{f"{campo}__isnull": True})
    return models.CheckConstraint(condition=condicion, name=f"{tabla}_{campo}_valido")


@deconstructible
class RutaAleatoria:
    """Guarda cada archivo con un nombre UUID dentro de la carpeta indicada (RNF-06)."""

    def __init__(self, carpeta):
        self.carpeta = carpeta

    def __call__(self, instancia, nombre_original):
        extension = os.path.splitext(nombre_original)[1].lower()
        return f"{self.carpeta}/{uuid.uuid4().hex}{extension}"

    def __eq__(self, otro):
        return isinstance(otro, RutaAleatoria) and self.carpeta == otro.carpeta
