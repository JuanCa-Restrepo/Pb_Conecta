from django.conf import settings
from django.db import models


class Notificacion(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notificaciones")
    tipo = models.CharField(max_length=50)
    titulo = models.CharField(max_length=150)
    mensaje = models.TextField()
    url_destino = models.CharField(max_length=300, blank=True)
    leida = models.BooleanField(default=False)
    enviada_correo = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notificacion"
        verbose_name = "notificación"
        verbose_name_plural = "notificaciones"
        ordering = ["-creado_en"]
        indexes = [models.Index(fields=["usuario", "leida", "-creado_en"], name="notificacion_campana_idx")]

    def __str__(self):
        return f"{self.titulo} → {self.usuario.email}"
