from django.conf import settings
from django.db import models

from apps.catalogos.models import Programa
from apps.comun.modelos import RutaAleatoria, ck_opciones
from apps.convocatorias.models import Convocatoria
from apps.empresas.models import Empresa


class PublicacionTipo(models.TextChoices):
    CONVOCATORIA = "CONVOCATORIA", "Convocatoria"
    OFERTA_EXTERNA = "OFERTA_EXTERNA", "Oferta externa / bolsa de empleo"
    EVENTO = "EVENTO", "Evento"
    NOTICIA = "NOTICIA", "Noticia"
    COMUNICADO = "COMUNICADO", "Comunicado de la oficina"


class PublicacionEstado(models.TextChoices):
    PUBLICADA = "PUBLICADA", "Publicada"
    OCULTA = "OCULTA", "Oculta por moderación"
    ELIMINADA = "ELIMINADA", "Eliminada por su autor"


class Publicacion(models.Model):
    Tipo = PublicacionTipo
    Estado = PublicacionEstado

    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="publicaciones")
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True, related_name="publicaciones")
    tipo = models.CharField(max_length=25, choices=Tipo.choices)
    titulo = models.CharField("título", max_length=200)
    texto = models.TextField()
    imagen = models.ImageField(upload_to=RutaAleatoria("publico/muro"), blank=True)
    enlace_url = models.URLField(max_length=500, blank=True)
    fuente_externa = models.CharField(max_length=150, blank=True)
    convocatoria = models.OneToOneField(
        Convocatoria, on_delete=models.CASCADE, null=True, blank=True, related_name="publicacion"
    )
    fecha_evento = models.DateTimeField(null=True, blank=True)
    lugar_evento = models.CharField(max_length=200, blank=True)
    para_todos_programas = models.BooleanField(default=True)
    estado = models.CharField(max_length=25, choices=Estado.choices, default=Estado.PUBLICADA)
    motivo_ocultamiento = models.TextField(blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    programas = models.ManyToManyField(Programa, db_table="publicacion_programa", related_name="publicaciones", blank=True)

    class Meta:
        db_table = "publicacion"
        verbose_name = "publicación"
        verbose_name_plural = "publicaciones"
        ordering = ["-creado_en"]
        indexes = [models.Index(fields=["estado", "-creado_en"], name="publicacion_feed_idx")]
        constraints = [
            ck_opciones("publicacion", "tipo", PublicacionTipo),
            ck_opciones("publicacion", "estado", PublicacionEstado),
            models.CheckConstraint(
                condition=~models.Q(tipo="CONVOCATORIA") | models.Q(convocatoria__isnull=False),
                name="publicacion_convocatoria_requerida",
            ),
            models.CheckConstraint(  # RF-104
                condition=~models.Q(tipo="OFERTA_EXTERNA") | ~models.Q(enlace_url=""),
                name="publicacion_oferta_externa_con_enlace",
            ),
            models.CheckConstraint(
                condition=~models.Q(tipo="EVENTO") | models.Q(fecha_evento__isnull=False),
                name="publicacion_evento_con_fecha",
            ),
            models.CheckConstraint(  # RN-11
                condition=~models.Q(estado="OCULTA") | ~models.Q(motivo_ocultamiento=""),
                name="publicacion_motivo_al_ocultar",
            ),
        ]

    def __str__(self):
        return self.titulo


class Comentario(models.Model):
    publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE, related_name="comentarios")
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    texto = models.CharField(max_length=1000)
    oculto = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "comentario"
        ordering = ["creado_en"]


class ReaccionTipo(models.TextChoices):
    ME_INTERESA = "ME_INTERESA", "Me interesa"


class Reaccion(models.Model):
    Tipo = ReaccionTipo

    publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE, related_name="reacciones")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    tipo = models.CharField(max_length=25, choices=Tipo.choices, default=Tipo.ME_INTERESA)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reaccion"
        verbose_name = "reacción"
        verbose_name_plural = "reacciones"
        constraints = [
            models.UniqueConstraint(fields=["publicacion", "usuario"], name="reaccion_unica_uq"),
            ck_opciones("reaccion", "tipo", ReaccionTipo),
        ]


class PublicacionGuardada(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "publicacion_guardada"
        constraints = [models.UniqueConstraint(fields=["usuario", "publicacion"], name="publicacion_guardada_uq")]
