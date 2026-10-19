"""Listas de valores compartidas entre varias apps."""

from django.db import models


class Modalidad(models.TextChoices):
    PRESENCIAL = "PRESENCIAL", "Presencial"
    REMOTA = "REMOTA", "Remota"
    HIBRIDA = "HIBRIDA", "Híbrida"


class TipoVinculacion(models.TextChoices):
    CONTRATO_APRENDIZAJE = "CONTRATO_APRENDIZAJE", "Contrato de aprendizaje"
    PRACTICA = "PRACTICA", "Práctica"
    PASANTIA = "PASANTIA", "Pasantía"
    VINCULO_LABORAL = "VINCULO_LABORAL", "Vínculo laboral"
