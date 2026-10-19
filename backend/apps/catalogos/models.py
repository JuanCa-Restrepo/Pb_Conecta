from django.db import models
from django.db.models.functions import Lower

from apps.comun.modelos import ck_opciones


class Facultad(models.Model):
    nombre = models.CharField(max_length=150, unique=True)

    class Meta:
        db_table = "facultad"
        verbose_name_plural = "facultades"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class ProgramaNivel(models.TextChoices):
    TECNICO = "TECNICO", "Técnico profesional"
    TECNOLOGICO = "TECNOLOGICO", "Tecnológico"
    PROFESIONAL = "PROFESIONAL", "Profesional"


class Programa(models.Model):
    Nivel = ProgramaNivel

    facultad = models.ForeignKey(Facultad, on_delete=models.PROTECT, related_name="programas")
    nombre = models.CharField(max_length=150)
    nivel = models.CharField(max_length=25, choices=Nivel.choices)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "programa"
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(fields=["nombre", "nivel"], name="programa_nombre_nivel_uq"),
            ck_opciones("programa", "nivel", ProgramaNivel),
        ]

    def __str__(self):
        return self.nombre


class HabilidadTipo(models.TextChoices):
    TECNICA = "TECNICA", "Técnica"
    BLANDA = "BLANDA", "Blanda"


class Habilidad(models.Model):
    Tipo = HabilidadTipo

    nombre = models.CharField(max_length=80)
    tipo = models.CharField(max_length=25, choices=Tipo.choices, default=Tipo.TECNICA)
    creada_por_usuario = models.BooleanField(default=False)

    class Meta:
        db_table = "habilidad"
        verbose_name_plural = "habilidades"
        ordering = ["nombre"]
        constraints = [
            models.UniqueConstraint(Lower("nombre"), name="habilidad_nombre_sin_mayusculas_uq"),
            ck_opciones("habilidad", "tipo", HabilidadTipo),
        ]

    def __str__(self):
        return self.nombre


class Sector(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "sector"
        verbose_name_plural = "sectores"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Ciudad(models.Model):
    nombre = models.CharField(max_length=100)
    departamento = models.CharField(max_length=100)

    class Meta:
        db_table = "ciudad"
        verbose_name_plural = "ciudades"
        ordering = ["nombre"]
        constraints = [models.UniqueConstraint(fields=["nombre", "departamento"], name="ciudad_nombre_depto_uq")]

    def __str__(self):
        return f"{self.nombre} ({self.departamento})"


class PeriodoAcademico(models.Model):
    codigo = models.CharField(max_length=10, unique=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    vigente = models.BooleanField(default=False)

    class Meta:
        db_table = "periodo_academico"
        verbose_name = "periodo académico"
        verbose_name_plural = "periodos académicos"
        ordering = ["-fecha_inicio"]
        constraints = [
            models.CheckConstraint(condition=models.Q(fecha_fin__gt=models.F("fecha_inicio")), name="periodo_fechas_validas"),
            models.UniqueConstraint(fields=["vigente"], condition=models.Q(vigente=True), name="periodo_un_solo_vigente"),
        ]

    def __str__(self):
        return self.codigo

    @classmethod
    def actual(cls):
        return cls.objects.filter(vigente=True).first()


class Parametro(models.Model):
    """Parámetros de negocio editables desde el admin (días de las alertas, etc.)."""

    clave = models.CharField(max_length=60, primary_key=True)
    valor = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True)

    class Meta:
        db_table = "parametro"
        verbose_name = "parámetro"

    def __str__(self):
        return f"{self.clave} = {self.valor}"

    @classmethod
    def entero(cls, clave, por_defecto):
        fila = cls.objects.filter(clave=clave).first()
        try:
            return int(fila.valor) if fila else por_defecto
        except ValueError:
            return por_defecto
