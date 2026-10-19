from django.conf import settings
from django.db import models

from apps.comun.modelos import RutaAleatoria, ck_opciones
from apps.comun.opciones import TipoVinculacion
from apps.convocatorias.models import Convocatoria
from apps.estudiantes.models import PerfilEstudiante


class EstadoPostulacion(models.TextChoices):
    POSTULADO = "POSTULADO", "Postulado"
    EN_REVISION = "EN_REVISION", "En revisión"
    PRESELECCIONADO = "PRESELECCIONADO", "Preseleccionado"
    ENTREVISTA = "ENTREVISTA", "Entrevista"
    SELECCIONADO = "SELECCIONADO", "Seleccionado"
    NO_SELECCIONADO = "NO_SELECCIONADO", "No seleccionado"
    RETIRADO = "RETIRADO", "Retirado"
    LEGALIZADO = "LEGALIZADO", "Legalizado"
    CERRADO_SISTEMA = "CERRADO_SISTEMA", "Cerrado por sistema"


ESTADOS_ACTIVOS = [
    EstadoPostulacion.POSTULADO,
    EstadoPostulacion.EN_REVISION,
    EstadoPostulacion.PRESELECCIONADO,
    EstadoPostulacion.ENTREVISTA,
    EstadoPostulacion.SELECCIONADO,
]


class Postulacion(models.Model):
    convocatoria = models.ForeignKey(Convocatoria, on_delete=models.PROTECT, related_name="postulaciones")
    estudiante = models.ForeignKey(PerfilEstudiante, on_delete=models.PROTECT, related_name="postulaciones")
    estado = models.CharField(max_length=25, choices=EstadoPostulacion.choices, default=EstadoPostulacion.POSTULADO)
    mensaje_presentacion = models.TextField(blank=True)
    hoja_vida = models.FileField(upload_to=RutaAleatoria("protegido/hv"))  # Copia enviada en el momento de postularse
    afinidad = models.PositiveSmallIntegerField(default=0)
    motivo_no_seleccion = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "postulacion"
        verbose_name = "postulación"
        verbose_name_plural = "postulaciones"
        ordering = ["-creado_en"]
        indexes = [
            models.Index(fields=["estudiante", "estado"], name="postulacion_est_estado_idx"),
            models.Index(fields=["convocatoria", "estado"], name="postulacion_conv_estado_idx"),
        ]
        constraints = [
            models.UniqueConstraint(fields=["convocatoria", "estudiante"], name="postulacion_unica_uq"),  # RN-06
            ck_opciones("postulacion", "estado", EstadoPostulacion),
            models.CheckConstraint(condition=models.Q(afinidad__lte=100), name="postulacion_afinidad_valida"),
            models.CheckConstraint(  # RN-11
                condition=~models.Q(estado="NO_SELECCIONADO") | ~models.Q(motivo_no_seleccion=""),
                name="postulacion_motivo_no_seleccion",
            ),
        ]

    def __str__(self):
        return f"{self.estudiante} → {self.convocatoria.titulo}"


class HistorialEstado(models.Model):
    """Trazabilidad de la postulación (RF-56). Solo inserción (RN-12)."""

    postulacion = models.ForeignKey(Postulacion, on_delete=models.CASCADE, related_name="historial")
    estado_anterior = models.CharField(max_length=25, choices=EstadoPostulacion.choices, null=True, blank=True)
    estado_nuevo = models.CharField(max_length=25, choices=EstadoPostulacion.choices)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+")
    comentario = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "historial_estado"
        verbose_name = "historial de estado"
        verbose_name_plural = "historial de estados"
        ordering = ["creado_en"]


class EntrevistaModalidad(models.TextChoices):
    PRESENCIAL = "PRESENCIAL", "Presencial"
    VIRTUAL = "VIRTUAL", "Virtual"
    TELEFONICA = "TELEFONICA", "Telefónica"


class EntrevistaEstado(models.TextChoices):
    PROGRAMADA = "PROGRAMADA", "Programada"
    REALIZADA = "REALIZADA", "Realizada"
    CANCELADA = "CANCELADA", "Cancelada"


class Entrevista(models.Model):
    Modalidad = EntrevistaModalidad
    Estado = EntrevistaEstado

    postulacion = models.ForeignKey(Postulacion, on_delete=models.CASCADE, related_name="entrevistas")
    fecha_hora = models.DateTimeField()
    modalidad = models.CharField(max_length=25, choices=Modalidad.choices)
    lugar_o_enlace = models.CharField(max_length=300)
    notas = models.TextField(blank=True)
    estado = models.CharField(max_length=25, choices=Estado.choices, default=Estado.PROGRAMADA)
    creada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "entrevista"
        ordering = ["fecha_hora"]
        constraints = [ck_opciones("entrevista", "modalidad", EntrevistaModalidad), ck_opciones("entrevista", "estado", EntrevistaEstado)]


class EntradaSeguimientoTipo(models.TextChoices):
    MENSAJE = "MENSAJE", "Mensaje"
    CONTACTO_EXTERNO = "CONTACTO_EXTERNO", "Contacto por fuera de la plataforma"
    NOTA_INTERNA = "NOTA_INTERNA", "Nota interna de la oficina"


class EntradaSeguimientoCanal(models.TextChoices):
    LLAMADA = "LLAMADA", "Llamada"
    CORREO = "CORREO", "Correo"
    WHATSAPP = "WHATSAPP", "WhatsApp"
    PRESENCIAL = "PRESENCIAL", "Presencial"
    OTRO = "OTRO", "Otro"


class EntradaSeguimiento(models.Model):
    """Bitácora de seguimiento compartida (RF-57). Solo inserción (RN-12)."""

    Tipo = EntradaSeguimientoTipo
    Canal = EntradaSeguimientoCanal

    postulacion = models.ForeignKey(Postulacion, on_delete=models.CASCADE, related_name="seguimiento")
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    tipo = models.CharField(max_length=25, choices=Tipo.choices, default=Tipo.MENSAJE)
    canal = models.CharField(max_length=25, choices=Canal.choices, null=True, blank=True)
    fecha_contacto = models.DateTimeField(null=True, blank=True)
    texto = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "entrada_seguimiento"
        verbose_name = "entrada de seguimiento"
        verbose_name_plural = "bitácora de seguimiento"
        ordering = ["creado_en"]
        constraints = [
            ck_opciones("entrada_seguimiento", "tipo", EntradaSeguimientoTipo),
            ck_opciones("entrada_seguimiento", "canal", EntradaSeguimientoCanal, nulo=True),
            models.CheckConstraint(
                condition=~models.Q(tipo="CONTACTO_EXTERNO")
                | models.Q(canal__isnull=False, fecha_contacto__isnull=False),
                name="entrada_seguimiento_contacto_completo",
            ),
        ]


class VerificacionRequisitosResultado(models.TextChoices):
    CUMPLE = "CUMPLE", "Cumple"
    NO_CUMPLE = "NO_CUMPLE", "No cumple"


class VerificacionRequisitos(models.Model):
    """Verificación en persona de la oficina antes de legalizar (RF-62a, RN-07). Solo inserción."""

    Resultado = VerificacionRequisitosResultado

    postulacion = models.ForeignKey(Postulacion, on_delete=models.CASCADE, related_name="verificaciones")
    funcionario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    resultado = models.CharField(max_length=25, choices=Resultado.choices)
    observacion = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "verificacion_requisitos"
        verbose_name = "verificación de requisitos"
        verbose_name_plural = "verificaciones de requisitos"
        ordering = ["-creado_en"]
        constraints = [
            ck_opciones("verificacion_requisitos", "resultado", VerificacionRequisitosResultado),
            models.CheckConstraint(
                condition=models.Q(resultado="CUMPLE") | ~models.Q(observacion=""),
                name="verificacion_observacion_si_no_cumple",
            ),
        ]


class PracticaEstado(models.TextChoices):
    LEGALIZADA = "LEGALIZADA", "Legalizada"
    EN_CURSO = "EN_CURSO", "En curso"
    FINALIZADA = "FINALIZADA", "Finalizada"
    CANCELADA = "CANCELADA", "Cancelada"


class Practica(models.Model):
    Estado = PracticaEstado

    postulacion = models.OneToOneField(Postulacion, on_delete=models.PROTECT, related_name="practica")
    estudiante = models.ForeignKey(PerfilEstudiante, on_delete=models.PROTECT, related_name="practicas")
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    tipo_vinculacion = models.CharField(max_length=25, choices=TipoVinculacion.choices)
    asesor_nombre = models.CharField(max_length=150)
    tutor_empresa_nombre = models.CharField(max_length=150)
    tutor_empresa_email = models.EmailField(max_length=254, blank=True)
    documento_soporte = models.FileField(upload_to=RutaAleatoria("protegido/practicas"), blank=True)
    estado = models.CharField(max_length=25, choices=Estado.choices, default=Estado.LEGALIZADA)
    observacion_cierre = models.TextField(blank=True)
    legalizada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    legalizada_en = models.DateTimeField(auto_now_add=True)
    finalizada_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "practica"
        verbose_name = "práctica"
        ordering = ["-legalizada_en"]
        constraints = [
            ck_opciones("practica", "estado", PracticaEstado),
            ck_opciones("practica", "tipo_vinculacion", TipoVinculacion),
            models.CheckConstraint(condition=models.Q(fecha_fin__gt=models.F("fecha_inicio")), name="practica_fechas_validas"),
            models.UniqueConstraint(  # RN-08: una sola práctica activa por estudiante
                fields=["estudiante"],
                condition=models.Q(estado__in=["LEGALIZADA", "EN_CURSO"]),
                name="practica_una_activa_por_estudiante",
            ),
        ]
