from django.contrib import admin

from .models import Convocatoria


@admin.register(Convocatoria)
class ConvocatoriaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "empresa", "estado", "modalidad", "cupos", "fecha_cierre")
    list_filter = ("estado", "modalidad", "tipo_vinculacion", "programas")
    search_fields = ("titulo", "empresa__razon_social")
    filter_horizontal = ("programas", "habilidades")
