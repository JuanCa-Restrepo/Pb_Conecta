from django.contrib import admin

from .models import Ciudad, Facultad, Habilidad, Parametro, PeriodoAcademico, Programa, Sector


@admin.register(Programa)
class ProgramaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "nivel", "facultad", "activo")
    list_filter = ("nivel", "facultad", "activo")
    search_fields = ("nombre",)


@admin.register(Habilidad)
class HabilidadAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "creada_por_usuario")
    list_filter = ("tipo", "creada_por_usuario")
    search_fields = ("nombre",)


@admin.register(PeriodoAcademico)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "fecha_inicio", "fecha_fin", "vigente")


@admin.register(Parametro)
class ParametroAdmin(admin.ModelAdmin):
    list_display = ("clave", "valor", "descripcion")


admin.site.register([Facultad, Sector, Ciudad])
