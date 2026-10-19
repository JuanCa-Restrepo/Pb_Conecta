from django.contrib import admin

from apps.comun.admin_utils import SoloLecturaAdmin

from .models import EntradaSeguimiento, Entrevista, HistorialEstado, Postulacion, Practica, VerificacionRequisitos


class HistorialInline(admin.TabularInline):
    model = HistorialEstado
    extra = 0
    can_delete = False
    readonly_fields = ("estado_anterior", "estado_nuevo", "usuario", "comentario", "creado_en")

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Postulacion)
class PostulacionAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "convocatoria", "estado", "afinidad", "creado_en")
    list_filter = ("estado",)
    search_fields = ("estudiante__usuario__email", "convocatoria__titulo")
    readonly_fields = ("estado",)  # Solo cambia por los servicios (RN-13)
    inlines = [HistorialInline]


@admin.register(Practica)
class PracticaAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "postulacion", "estado", "fecha_inicio", "fecha_fin")
    list_filter = ("estado",)


@admin.register(EntradaSeguimiento)
class EntradaSeguimientoAdmin(SoloLecturaAdmin):
    list_display = ("postulacion", "tipo", "canal", "autor", "creado_en")


@admin.register(VerificacionRequisitos)
class VerificacionAdmin(SoloLecturaAdmin):
    list_display = ("postulacion", "resultado", "funcionario", "creado_en")


admin.site.register(Entrevista)
