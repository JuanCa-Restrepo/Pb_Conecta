"""Permisos por rol (docs/02-arquitectura.md, sección 3.4). Los permisos por objeto se aplican filtrando querysets."""

from rest_framework.permissions import BasePermission

from apps.cuentas.models import Rol


class _PorRol(BasePermission):
    roles = ()

    def has_permission(self, request, view):
        usuario = request.user
        return bool(usuario and usuario.is_authenticated and usuario.rol in self.roles)


class EsEstudiante(_PorRol):
    roles = (Rol.ESTUDIANTE,)


class EsEmpresa(_PorRol):
    roles = (Rol.EMPRESA,)


class EsOficina(_PorRol):
    roles = (Rol.OFICINA, Rol.SUPERADMIN)


class EsSuperadmin(_PorRol):
    roles = (Rol.SUPERADMIN,)


class EsEmpresaAliada(EsEmpresa):
    """Empresa aprobada y con convenio vigente (RN-02)."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        vinculo = getattr(request.user, "vinculo_empresa", None)
        return bool(vinculo and vinculo.empresa.puede_publicar)
