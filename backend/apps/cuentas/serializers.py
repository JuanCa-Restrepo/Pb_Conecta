from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.catalogos.models import Ciudad, Programa, Sector
from apps.empresas.models import Empresa

from .models import Usuario
from .servicios import es_correo_institucional


class _BaseRegistro(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    nombres = serializers.CharField(max_length=100)
    apellidos = serializers.CharField(max_length=100)
    telefono = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    acepta_politica = serializers.BooleanField(write_only=True)

    def validate_email(self, valor):
        valor = valor.lower()
        if Usuario.objects.filter(email__iexact=valor).exists():
            raise serializers.ValidationError("Ya existe una cuenta con este correo.")
        return valor

    def validate_acepta_politica(self, valor):
        if not valor:
            raise serializers.ValidationError("Debes aceptar la política de tratamiento de datos (Ley 1581 de 2012).")
        return valor

    def validate(self, datos):
        usuario_temporal = Usuario(email=datos["email"], nombres=datos["nombres"], apellidos=datos["apellidos"])
        try:
            validate_password(datos["password"], user=usuario_temporal)
        except Exception as error:  # ValidationError de Django → error del campo password
            raise serializers.ValidationError({"password": list(getattr(error, "messages", [str(error)]))})
        return datos


class RegistroEstudianteSerializer(_BaseRegistro):
    programa = serializers.PrimaryKeyRelatedField(queryset=Programa.objects.filter(activo=True))
    documento = serializers.CharField(max_length=20, required=False, allow_blank=True)
    semestre = serializers.IntegerField(min_value=1, max_value=12, required=False, allow_null=True)

    def validate_email(self, valor):
        valor = super().validate_email(valor)
        if not es_correo_institucional(valor):
            raise serializers.ValidationError(f"Usa tu correo institucional @{settings.DOMINIO_INSTITUCIONAL}.")
        return valor


class RegistroEmpresaSerializer(_BaseRegistro):
    cargo = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    razon_social = serializers.CharField(max_length=200)
    nit = serializers.RegexField(r"^\d{6,12}(-\d)?$", max_length=15, error_messages={"invalid": "Formato de NIT no válido. Ejemplo: 900123456-7"})
    sector = serializers.PrimaryKeyRelatedField(queryset=Sector.objects.all())
    ciudad = serializers.PrimaryKeyRelatedField(queryset=Ciudad.objects.all())
    sitio_web = serializers.URLField(required=False, allow_blank=True, default="")
    descripcion = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_nit(self, valor):
        if Empresa.objects.filter(nit=valor).exists():
            raise serializers.ValidationError("Ya existe una empresa registrada con este NIT.")
        return valor


class VerificarCorreoSerializer(serializers.Serializer):
    token = serializers.CharField()


class InicioSesionSerializer(TokenObtainPairSerializer):
    default_error_messages = {
        "no_active_account": "Correo o contraseña incorrectos, o la cuenta aún no está activa (revisa tu correo).",
    }

    @classmethod
    def get_token(cls, usuario):
        token = super().get_token(usuario)
        token["rol"] = usuario.rol
        token["nombre"] = usuario.nombres
        return token


class UsuarioActualSerializer(serializers.ModelSerializer):
    rol_nombre = serializers.CharField(source="get_rol_display", read_only=True)
    estudiante = serializers.SerializerMethodField()
    empresa = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ["id", "email", "nombres", "apellidos", "telefono", "foto", "rol", "rol_nombre", "estudiante", "empresa"]

    def get_estudiante(self, usuario):
        perfil = getattr(usuario, "perfil_estudiante", None)
        if perfil is None:
            return None
        ultima = perfil.habilitaciones.select_related("periodo").first()
        return {
            "id": perfil.pk,
            "programa": perfil.programa_id,
            "programa_nombre": perfil.programa.nombre,
            "estado": perfil.estado,
            "estado_nombre": perfil.get_estado_display(),
            "habilitacion": {
                "accion": ultima.accion,
                "periodo": ultima.periodo.codigo,
                "fecha": ultima.creado_en,
                "observacion": ultima.observacion,
            } if ultima else None,
        }

    def get_empresa(self, usuario):
        vinculo = getattr(usuario, "vinculo_empresa", None)
        if vinculo is None:
            return None
        empresa = vinculo.empresa
        return {
            "id": empresa.pk,
            "razon_social": empresa.razon_social,
            "estado": empresa.estado,
            "estado_nombre": empresa.get_estado_display(),
            "puede_publicar": empresa.puede_publicar,
        }
