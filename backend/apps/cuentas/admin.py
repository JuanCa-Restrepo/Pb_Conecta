from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import BaseUserCreationForm, UserChangeForm
from django.utils import timezone

from .models import ConsentimientoDatos, Rol, Usuario


class CrearUsuarioForm(BaseUserCreationForm):
    class Meta:
        model = Usuario
        fields = ("email", "nombres", "apellidos", "rol")


class EditarUsuarioForm(UserChangeForm):
    class Meta:
        model = Usuario
        fields = "__all__"


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """RF-03: el superadministrador crea aquí las cuentas de la oficina de prácticas."""

    add_form = CrearUsuarioForm
    form = EditarUsuarioForm
    ordering = ("email",)
    list_display = ("email", "nombres", "apellidos", "rol", "is_active")
    list_filter = ("rol", "is_active")
    search_fields = ("email", "nombres", "apellidos")
    readonly_fields = ("creado_en", "last_login")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Datos personales", {"fields": ("nombres", "apellidos", "telefono", "foto", "rol")}),
        ("Estado y permisos", {"fields": ("is_active", "is_staff", "is_superuser", "email_verificado_en")}),
        ("Fechas", {"fields": ("creado_en", "last_login")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "nombres", "apellidos", "rol", "password1", "password2")}),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Las cuentas creadas por el superadmin no requieren verificar el correo
            obj.is_active = True
            obj.email_verificado_en = timezone.now()
            obj.is_staff = obj.rol == Rol.SUPERADMIN
        super().save_model(request, obj, form, change)


@admin.register(ConsentimientoDatos)
class ConsentimientoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "version_politica", "aceptado_en", "ip")
