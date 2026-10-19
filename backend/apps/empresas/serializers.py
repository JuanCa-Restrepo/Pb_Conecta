from django.utils import timezone
from rest_framework import serializers

from apps.catalogos.models import Ciudad, Sector
from apps.comun.archivos import validar_pdf

from .models import Convenio, Empresa


class ConvenioSerializer(serializers.ModelSerializer):
    vigente = serializers.SerializerMethodField()
    tiene_documento = serializers.SerializerMethodField()
    registrado_por_nombre = serializers.CharField(source="registrado_por.nombre_completo", read_only=True)

    class Meta:
        model = Convenio
        fields = ["id", "numero", "fecha_inicio", "fecha_fin", "vigente", "tiene_documento", "registrado_por_nombre", "creado_en"]

    def get_vigente(self, convenio):
        return convenio.fecha_inicio <= timezone.localdate() <= convenio.fecha_fin

    def get_tiene_documento(self, convenio):
        return bool(convenio.documento)


class DatosConvenioSerializer(serializers.Serializer):
    """Entrada para aprobar una empresa o registrar un convenio (multipart, con PDF opcional)."""

    numero = serializers.CharField(max_length=50)
    fecha_inicio = serializers.DateField()
    fecha_fin = serializers.DateField()
    documento = serializers.FileField(required=False, validators=[validar_pdf])

    def validate_numero(self, valor):
        if Convenio.objects.filter(numero__iexact=valor).exists():
            raise serializers.ValidationError("Ya existe un convenio con este número.")
        return valor


class MotivoSerializer(serializers.Serializer):
    motivo = serializers.CharField(allow_blank=True, required=False, default="")


class EmpresaListaSerializer(serializers.ModelSerializer):
    sector_nombre = serializers.CharField(source="sector.nombre", read_only=True)
    ciudad_nombre = serializers.CharField(source="ciudad.nombre", read_only=True)
    estado_nombre = serializers.CharField(source="get_estado_display", read_only=True)
    convenio_vigente = serializers.SerializerMethodField()
    puede_publicar = serializers.BooleanField(read_only=True)

    class Meta:
        model = Empresa
        fields = [
            "id", "razon_social", "nit", "sector_nombre", "ciudad_nombre", "estado", "estado_nombre", "motivo_estado",
            "convenio_vigente", "puede_publicar", "creada_por_oficina", "contacto_nombre", "contacto_email",
            "contacto_telefono", "creado_en",
        ]

    def get_convenio_vigente(self, empresa):
        convenio = empresa.convenio_vigente()
        return {"numero": convenio.numero, "fecha_fin": convenio.fecha_fin} if convenio else None


class EmpresaDetalleSerializer(EmpresaListaSerializer):
    convenios = ConvenioSerializer(many=True, read_only=True)
    usuarios = serializers.SerializerMethodField()
    tamano_nombre = serializers.CharField(source="get_tamano_display", read_only=True)

    class Meta(EmpresaListaSerializer.Meta):
        fields = EmpresaListaSerializer.Meta.fields + [
            "descripcion", "sitio_web", "direccion", "tamano", "tamano_nombre", "convenios", "usuarios",
        ]

    def get_usuarios(self, empresa):
        return [
            {"nombre": v.usuario.nombre_completo, "email": v.usuario.email, "cargo": v.cargo, "activo": v.usuario.is_active}
            for v in empresa.usuarios.select_related("usuario")
        ]


class CrearEmpresaSerializer(serializers.Serializer):
    """RF-24: la oficina registra una empresa con su convenio en un solo paso."""

    razon_social = serializers.CharField(max_length=200)
    nit = serializers.RegexField(r"^\d{6,12}(-\d)?$", max_length=15, error_messages={"invalid": "Formato de NIT no válido. Ejemplo: 900123456-7"})
    sector = serializers.PrimaryKeyRelatedField(queryset=Sector.objects.all())
    ciudad = serializers.PrimaryKeyRelatedField(queryset=Ciudad.objects.all())
    contacto_nombre = serializers.CharField(max_length=150)
    contacto_email = serializers.EmailField()
    contacto_telefono = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    sitio_web = serializers.URLField(required=False, allow_blank=True, default="")
    descripcion = serializers.CharField(required=False, allow_blank=True, default="")
    numero = serializers.CharField(max_length=50)
    fecha_inicio = serializers.DateField()
    fecha_fin = serializers.DateField()
    documento = serializers.FileField(required=False, validators=[validar_pdf])

    validate_numero = DatosConvenioSerializer.validate_numero

    def validate_nit(self, valor):
        if Empresa.objects.filter(nit=valor).exists():
            raise serializers.ValidationError("Ya existe una empresa registrada con este NIT.")
        return valor
