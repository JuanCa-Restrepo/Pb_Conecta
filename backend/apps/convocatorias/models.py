from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models

from apps.catalogos.models import Ciudad, Habilidad, Programa
from apps.comun.modelos import ck_opciones
from apps.comun.opciones import Modalidad, TipoVinculacion
from apps.empresas.models import Empresa


class ConvocatoriaNivelFormacion(models.TextChoices):
    TECNICO = "TECNICO", "Técnico profesional"
    TECNOLOGICO = "TECNOLOGICO", "Tecnológico"
    PROFESIONAL = "PROFESIONAL", "Profesional"
    CUALQUIERA = "CUALQUIERA", "Cualquier nivel"


class ConvocatoriaEstado(models.TextChoices):
    BORRADOR = "BORRADOR", "Borrador"
    EN_REVISION = "EN_REVISION", "En revisión"
    DEVUELTA = "DEVUELTA", "Devuelta con observaciones"
    PUBLICADA = "PUBLICADA", "Publicada"
    CERRADA = "CERRADA", "Cerrada"
    CANCELADA = "CANCELADA", "Cancelada"


class ConvocatoriaMotivoCierre(models.TextChoices):
    FECHA = "FECHA", "Fecha de cierre"
    CUPOS = "CUPOS", "Cupos completos"
    MANUAL = "MANUAL", "Cierre manual"


class Convocatoria(models.Model):
    NivelFormacion = ConvocatoriaNivelFormacion
    Estado = ConvocatoriaEstado
    MotivoCierre = ConvocatoriaMotivoCierre

    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT, related_name="convocatorias")
    creada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    titulo = models.CharField("título", max_length=150)
    descripcion = models.TextField("descripción")
    funciones = models.TextField()
    nivel_formacion = models.CharField(max_length=25, choices=NivelFormacion.choices, default=NivelFormacion.CUALQUIERA)
    modalidad = models.CharField(max_length=25, choices=Modalidad.choices)
    ciudad = models.ForeignKey(Ciudad, on_delete=models.PROTECT, null=True, blank=True)  # Nula si es remota
    tipo_vinculacion = models.CharField(max_length=25, choices=TipoVinculacion.choices)
    apoyo_economico = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # COP
    cupos = models.PositiveSmallIntegerField(default=1)
    fecha_inicio = models.DateField()
    duracion_meses = models.PositiveSmallIntegerField(default=6)
    fecha_cierre = models.DateField()
    estado = models.CharField(max_length=25, choices=Estado.choices, default=Estado.BORRADOR)
    observacion_revision = models.TextField(blank=True)
    motivo_cierre = models.CharField(max_length=25, choices=MotivoCierre.choices, null=True, blank=True)
    publicada_en = models.DateTimeField(null=True, blank=True)
    search_vector = SearchVectorField(null=True, editable=False)  # Búsqueda de texto completo (arquitectura 3.6)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    programas = models.ManyToManyField(Programa, db_table="convocatoria_programa", related_name="convocatorias")
    habilidades = models.ManyToManyField(Habilidad, db_table="convocatoria_habilidad", related_name="convocatorias", blank=True)

    class Meta:
        db_table = "convocatoria"
        ordering = ["-publicada_en", "-creado_en"]
        indexes = [
            models.Index(fields=["estado", "fecha_cierre"], name="convocatoria_estado_cierre_idx"),
            GinIndex(fields=["search_vector"], name="convocatoria_busqueda_gin"),
        ]
        constraints = [
            ck_opciones("convocatoria", "nivel_formacion", ConvocatoriaNivelFormacion),
            ck_opciones("convocatoria", "modalidad", Modalidad),
            ck_opciones("convocatoria", "tipo_vinculacion", TipoVinculacion),
            ck_opciones("convocatoria", "estado", ConvocatoriaEstado),
            ck_opciones("convocatoria", "motivo_cierre", ConvocatoriaMotivoCierre, nulo=True),
            models.CheckConstraint(condition=models.Q(cupos__gt=0), name="convocatoria_cupos_positivos"),
            models.CheckConstraint(
                condition=models.Q(duracion_meses__gte=1, duracion_meses__lte=24), name="convocatoria_duracion_valida"
            ),
            models.CheckConstraint(
                condition=models.Q(apoyo_economico__isnull=True) | models.Q(apoyo_economico__gte=0),
                name="convocatoria_apoyo_no_negativo",
            ),
            models.CheckConstraint(  # RN-11: observación obligatoria al devolver
                condition=~models.Q(estado="DEVUELTA") | ~models.Q(observacion_revision=""),
                name="convocatoria_observacion_al_devolver",
            ),
        ]

    def __str__(self):
        return f"{self.titulo} · {self.empresa}"


class ConvocatoriaGuardada(models.Model):
    estudiante = models.ForeignKey("estudiantes.PerfilEstudiante", on_delete=models.CASCADE, related_name="convocatorias_guardadas")
    convocatoria = models.ForeignKey(Convocatoria, on_delete=models.CASCADE)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "convocatoria_guardada"
        constraints = [models.UniqueConstraint(fields=["estudiante", "convocatoria"], name="convocatoria_guardada_uq")]
