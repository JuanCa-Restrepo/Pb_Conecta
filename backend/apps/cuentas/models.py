from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.db.models.functions import Lower

from apps.comun.modelos import RutaAleatoria, ck_opciones


class Rol(models.TextChoices):
    ESTUDIANTE = "ESTUDIANTE", "Estudiante"
    EMPRESA = "EMPRESA", "Empresa"
    OFICINA = "OFICINA", "Oficina de prácticas"
    SUPERADMIN = "SUPERADMIN", "Superadministrador"


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    def _crear(self, email, password, **campos):
        if not email:
            raise ValueError("El correo es obligatorio")
        usuario = self.model(email=self.normalize_email(email).lower(), **campos)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_user(self, email, password=None, **campos):
        campos.setdefault("rol", Rol.ESTUDIANTE)
        return self._crear(email, password, **campos)

    def create_superuser(self, email, password, **campos):
        campos.update(rol=Rol.SUPERADMIN, is_active=True, is_staff=True, is_superuser=True)
        return self._crear(email, password, **campos)


class Usuario(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("correo", max_length=254, unique=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, blank=True)
    foto = models.ImageField(upload_to=RutaAleatoria("publico/fotos"), blank=True)
    rol = models.CharField(max_length=25, choices=Rol.choices)
    is_active = models.BooleanField("activo", default=False)  # Se activa al verificar el correo
    is_staff = models.BooleanField("acceso al admin", default=False)
    email_verificado_en = models.DateTimeField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    objects = UsuarioManager()

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["nombres", "apellidos"]

    class Meta:
        db_table = "usuario"
        verbose_name = "usuario"
        constraints = [
            models.UniqueConstraint(Lower("email"), name="usuario_email_sin_mayusculas_uq"),
            ck_opciones("usuario", "rol", Rol),
        ]

    def __str__(self):
        return f"{self.nombre_completo} <{self.email}>"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}".strip()


class ConsentimientoDatos(models.Model):
    """Aceptación de la política de tratamiento de datos, Ley 1581 de 2012 (RF-06)."""

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="consentimientos")
    version_politica = models.CharField(max_length=20)
    aceptado_en = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = "consentimiento_datos"
        verbose_name = "consentimiento de datos"
        verbose_name_plural = "consentimientos de datos"
