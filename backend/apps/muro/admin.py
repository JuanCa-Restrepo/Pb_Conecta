from django.contrib import admin

from .models import Comentario, Publicacion


@admin.register(Publicacion)
class PublicacionAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "autor", "estado", "creado_en")
    list_filter = ("tipo", "estado")
    search_fields = ("titulo", "texto")
    filter_horizontal = ("programas",)


admin.site.register(Comentario)
