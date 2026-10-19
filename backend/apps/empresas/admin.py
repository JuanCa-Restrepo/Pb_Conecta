from django.contrib import admin

from .models import Convenio, Empresa, UsuarioEmpresa


class ConvenioInline(admin.TabularInline):
    model = Convenio
    extra = 0


class UsuarioEmpresaInline(admin.TabularInline):
    model = UsuarioEmpresa
    extra = 0


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("razon_social", "nit", "sector", "ciudad", "estado")
    list_filter = ("estado", "sector")
    search_fields = ("razon_social", "nit")
    inlines = [ConvenioInline, UsuarioEmpresaInline]


@admin.register(Convenio)
class ConvenioAdmin(admin.ModelAdmin):
    list_display = ("numero", "empresa", "fecha_inicio", "fecha_fin")
    search_fields = ("numero", "empresa__razon_social")
