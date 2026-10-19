from django.contrib import admin

from apps.comun.admin_utils import SoloLecturaAdmin

from .models import (
    Certificacion, Enlace, EstudianteHabilidad, Experiencia, Habilitacion, IdiomaEstudiante, NotaAsesoria,
    PerfilEstudiante, Proyecto,
)


class HabilidadInline(admin.TabularInline):
    model = EstudianteHabilidad
    extra = 0


class IdiomaInline(admin.TabularInline):
    model = IdiomaEstudiante
    extra = 0


class ExperienciaInline(admin.StackedInline):
    model = Experiencia
    extra = 0


@admin.register(PerfilEstudiante)
class PerfilEstudianteAdmin(admin.ModelAdmin):
    list_display = ("__str__", "programa", "semestre", "estado", "abierto_oportunidades")
    list_filter = ("estado", "programa__facultad", "programa")
    search_fields = ("usuario__email", "usuario__nombres", "usuario__apellidos", "documento")
    readonly_fields = ("estado",)  # Solo cambia por los servicios (RN-15)
    inlines = [HabilidadInline, IdiomaInline, ExperienciaInline]


@admin.register(Habilitacion)
class HabilitacionAdmin(SoloLecturaAdmin):
    list_display = ("estudiante", "accion", "periodo", "funcionario", "creado_en")
    list_filter = ("accion", "periodo")


admin.site.register([Proyecto, Certificacion, Enlace, NotaAsesoria])
