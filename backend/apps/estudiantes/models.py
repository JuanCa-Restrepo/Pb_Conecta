from django.conf import settings
from django.db import models

from apps.catalogos.models import Ciudad, Habilidad, PeriodoAcademico, Programa
from apps.comun.modelos import RutaAleatoria, ck_opciones
from apps.comun.opciones import Modalidad


class EstadoEstudiante(models.TextChoices):
    NO_HABILITADO = "NO_HABILITADO", "No habilitado"
    HABILITADO = "HABILITADO", "Habilitado"
    UBICADO = "UBICADO", "Ubicado"
    EN_PRACTICA = "EN_PRACTICA", "En práctica"
    PRACTICA_FINALIZADA = "PRACTICA_FINALIZADA", "Práctica finalizada"


class PerfilEstudianteJornada(models.TextChoices):
    COMPLETA = "COMPLETA", "Tiempo completo"
    MEDIA = "MEDIA", "Medio tiempo"
    FLEXIBLE = "FLEXIBLE", "Flexible"


class PerfilEstudiante(models.Model):
    Jornada = PerfilEstudianteJornada

    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil_estudiante")
    programa = models.ForeignKey(Programa, on_delete=models.PROTECT, related_name="estudiantes")
    documento = models.CharField(max_length=20, unique=True, null=True, blank=True)  # Nunca se envía a empresas
    semestre = models.PositiveSmallIntegerField(null=True, blank=True)
    ciudad = models.ForeignKey(Ciudad, on_delete=models.SET_NULL, null=True, blank=True)
    titular = models.CharField(max_length=150, blank=True)
    acerca_de = models.TextField(blank=True)
    hoja_vida = models.FileField(upload_to=RutaAleatoria("protegido/hv"), blank=True)
    fecha_disponible = models.DateField(null=True, blank=True)
    jornada = models.CharField(max_length=25, choices=Jornada.choices, null=True, blank=True)
    modalidad_preferida = models.CharField(max_length=25, choices=Modalidad.choices, null=True, blank=True)
    abierto_oportunidades = models.BooleanField(default=False)
    estado = models.CharField(max_length=25, choices=EstadoEstudiante.choices, default=EstadoEstudiante.NO_HABILITADO)
    actualizado_en = models.DateTimeField(auto_now=True)

    habilidades = models.ManyToManyField(Habilidad, through="EstudianteHabilidad", related_name="estudiantes")

    class Meta:
        db_table = "perfil_estudiante"
        verbose_name = "perfil de estudiante"
        verbose_name_plural = "perfiles de estudiantes"
        indexes = [models.Index(fields=["estado"], name="perfil_estudiante_estado_idx")]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(semestre__isnull=True) | models.Q(semestre__gte=1, semestre__lte=12),
                name="perfil_estudiante_semestre_valido",
            ),
            ck_opciones("perfil_estudiante", "jornada", PerfilEstudianteJornada, nulo=True),
            ck_opciones("perfil_estudiante", "modalidad_preferida", Modalidad, nulo=True),
            ck_opciones("perfil_estudiante", "estado", EstadoEstudiante),
        ]

    def __str__(self):
        return self.usuario.nombre_completo


class EstudianteHabilidadNivel(models.TextChoices):
    BASICO = "BASICO", "Básico"
    INTERMEDIO = "INTERMEDIO", "Intermedio"
    AVANZADO = "AVANZADO", "Avanzado"


class EstudianteHabilidad(models.Model):
    Nivel = EstudianteHabilidadNivel

    estudiante = models.ForeignKey(PerfilEstudiante, on_delete=models.CASCADE)
    habilidad = models.ForeignKey(Habilidad, on_delete=models.CASCADE)
    nivel = models.CharField(max_length=25, choices=Nivel.choices, default=Nivel.BASICO)

    class Meta:
        db_table = "estudiante_habilidad"
        constraints = [
            models.UniqueConstraint(fields=["estudiante", "habilidad"], name="estudiante_habilidad_uq"),
            ck_opciones("estudiante_habilidad", "nivel", EstudianteHabilidadNivel),
        ]


class IdiomaEstudianteNivel(models.TextChoices):
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"
    NATIVO = "NATIVO", "Nativo"


class IdiomaEstudiante(models.Model):
    Nivel = IdiomaEstudianteNivel

    estudiante = models.ForeignKey(PerfilEstudiante, on_delete=models.CASCADE, related_name="idiomas")
    idioma = models.CharField(max_length=50)
    nivel = models.CharField(max_length=10, choices=Nivel.choices)

    class Meta:
        db_table = "idioma_estudiante"
        constraints = [
            models.UniqueConstraint(fields=["estudiante", "idioma"], name="idioma_estudiante_uq"),
            ck_opciones("idioma_estudiante", "nivel", IdiomaEstudianteNivel),
        ]


class Experiencia(models.Model):
    estudiante = models.ForeignKey(PerfilEstudiante, on_delete=models.CASCADE, related_name="experiencias")
    cargo = models.CharField(max_length=120)
    organizacion = models.CharField(max_length=150)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)  # Nula = trabajo actual
    descripcion = models.TextField(blank=True)

    class Meta:
        db_table = "experiencia"
        ordering = ["-fecha_inicio"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(fecha_fin__isnull=True) | models.Q(fecha_fin__gte=models.F("fecha_inicio")),
                name="experiencia_fechas_validas",
            )
        ]


class Proyecto(models.Model):
    estudiante = models.ForeignKey(PerfilEstudiante, on_delete=models.CASCADE, related_name="proyectos")
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)
    url = models.URLField(max_length=300, blank=True)

    class Meta:
        db_table = "proyecto"


class Certificacion(models.Model):
    estudiante = models.ForeignKey(PerfilEstudiante, on_delete=models.CASCADE, related_name="certificaciones")
    nombre = models.CharField(max_length=150)
    entidad = models.CharField(max_length=150)
    fecha = models.DateField(null=True, blank=True)
    url = models.URLField(max_length=300, blank=True)

    class Meta:
        db_table = "certificacion"
        verbose_name_plural = "certificaciones"


class EnlaceTipo(models.TextChoices):
    LINKEDIN = "LINKEDIN", "LinkedIn"
    GITHUB = "GITHUB", "GitHub"
    PORTAFOLIO = "PORTAFOLIO", "Portafolio"
    OTRO = "OTRO", "Otro"


class Enlace(models.Model):
    Tipo = EnlaceTipo

    estudiante = models.ForeignKey(PerfilEstudiante, on_delete=models.CASCADE, related_name="enlaces")
    tipo = models.CharField(max_length=25, choices=Tipo.choices)
    url = models.URLField(max_length=300)

    class Meta:
        db_table = "enlace"
        constraints = [ck_opciones("enlace", "tipo", EnlaceTipo)]


class HabilitacionAccion(models.TextChoices):
    HABILITADO = "HABILITADO", "Habilitado"
    DESHABILITADO = "DESHABILITADO", "Deshabilitado"


class Habilitacion(models.Model):
    """Historial de habilitaciones hecho por la oficina (RF-62). Solo inserción (RN-12)."""

    Accion = HabilitacionAccion

    estudiante = models.ForeignKey(PerfilEstudiante, on_delete=models.CASCADE, related_name="habilitaciones")
    periodo = models.ForeignKey(PeriodoAcademico, on_delete=models.PROTECT)
    accion = models.CharField(max_length=25, choices=Accion.choices)
    funcionario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    observacion = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "habilitacion"
        verbose_name = "habilitación"
        verbose_name_plural = "habilitaciones"
        ordering = ["-creado_en"]
        indexes = [models.Index(fields=["estudiante", "creado_en"], name="habilitacion_est_fecha_idx")]
        constraints = [
            ck_opciones("habilitacion", "accion", HabilitacionAccion),
            models.CheckConstraint(  # RN-11: motivo obligatorio al deshabilitar
                condition=models.Q(accion="HABILITADO") | ~models.Q(observacion=""),
                name="habilitacion_motivo_al_deshabilitar",
            ),
        ]


class NotaAsesoria(models.Model):
    estudiante = models.ForeignKey(PerfilEstudiante, on_delete=models.CASCADE, related_name="notas_asesoria")
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    texto = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "nota_asesoria"
        verbose_name = "nota de asesoría"
        verbose_name_plural = "notas de asesoría"
        ordering = ["-creado_en"]
