"""Directorio de empresas aliadas y su página pública (RF-21, RF-22), seguir empresas (RF-23) y perfil propio (RF-20)."""

from django.db.models import Count, Q
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comun.archivos import validar_imagen
from apps.comun.permisos import EsEmpresa, EsEstudiante
from apps.convocatorias.models import Convocatoria
from apps.cuentas.models import Rol
from apps.muro.models import Publicacion

from .models import Empresa, EmpresaSeguida


class EmpresaPublicaSerializer(serializers.ModelSerializer):
    """Sin NIT ni datos de contacto: el estudiante ve el contacto solo desde la preselección (RF-58)."""

    sector_nombre = serializers.CharField(source="sector.nombre")
    ciudad_nombre = serializers.CharField(source="ciudad.nombre")
    tamano_nombre = serializers.CharField(source="get_tamano_display", default=None)
    logo = serializers.SerializerMethodField()
    convocatorias_activas = serializers.IntegerField(default=0)
    seguida = serializers.SerializerMethodField()

    class Meta:
        model = Empresa
        fields = ["id", "razon_social", "sector", "sector_nombre", "ciudad", "ciudad_nombre", "tamano_nombre", "descripcion",
                  "logo", "sitio_web", "convocatorias_activas", "seguida"]

    def get_logo(self, empresa):
        return empresa.logo.url if empresa.logo else None

    def get_seguida(self, empresa):
        seguidas = self.context.get("seguidas")
        return None if seguidas is None else empresa.pk in seguidas


class EmpresaPaginaSerializer(EmpresaPublicaSerializer):
    convocatorias = serializers.SerializerMethodField()
    publicaciones = serializers.SerializerMethodField()

    class Meta(EmpresaPublicaSerializer.Meta):
        fields = EmpresaPublicaSerializer.Meta.fields + ["convocatorias", "publicaciones"]

    def get_convocatorias(self, empresa):
        publicadas = empresa.convocatorias.filter(estado=Convocatoria.Estado.PUBLICADA).prefetch_related("programas").select_related("ciudad")
        return [
            {"id": c.id, "titulo": c.titulo, "modalidad_nombre": c.get_modalidad_display(),
             "ciudad_nombre": c.ciudad.nombre if c.ciudad else None, "fecha_cierre": c.fecha_cierre,
             "apoyo_economico": c.apoyo_economico, "programas": [p.nombre for p in c.programas.all()]}
            for c in publicadas.order_by("-publicada_en")
        ]

    def get_publicaciones(self, empresa):
        recientes = empresa.publicaciones.filter(estado=Publicacion.Estado.PUBLICADA).exclude(tipo=Publicacion.Tipo.CONVOCATORIA)
        return [{"id": p.id, "tipo_nombre": p.get_tipo_display(), "titulo": p.titulo, "texto": p.texto[:280], "creado_en": p.creado_en}
                for p in recientes.order_by("-creado_en")[:5]]


class EmpresasPublicasViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Público (también para visitantes sin sesión). Solo empresas aliadas con convenio vigente."""

    permission_classes = [AllowAny]

    def get_queryset(self):
        consulta = Empresa.objects.filter(estado=Empresa.Estado.ALIADA).select_related("sector", "ciudad").annotate(
            convocatorias_activas=Count("convocatorias", filter=Q(convocatorias__estado=Convocatoria.Estado.PUBLICADA))
        )
        parametros = self.request.query_params
        if texto := parametros.get("q", "").strip():
            consulta = consulta.filter(Q(razon_social__icontains=texto) | Q(descripcion__icontains=texto))
        for filtro in ("sector", "ciudad"):
            if valor := parametros.get(filtro):
                consulta = consulta.filter(**{filtro: valor})
        if parametros.get("seguidas") == "1" and self._perfil:
            consulta = consulta.filter(empresaseguida__estudiante=self._perfil)
        return consulta.order_by("-convocatorias_activas", "razon_social")

    @property
    def _perfil(self):
        usuario = self.request.user
        return usuario.perfil_estudiante if usuario.is_authenticated and usuario.rol == Rol.ESTUDIANTE else None

    def get_serializer_class(self):
        return EmpresaPaginaSerializer if self.action == "retrieve" else EmpresaPublicaSerializer

    def get_serializer_context(self):
        contexto = super().get_serializer_context()
        if self._perfil:
            contexto["seguidas"] = set(EmpresaSeguida.objects.filter(estudiante=self._perfil).values_list("empresa_id", flat=True))
        return contexto

    @action(detail=True, methods=["post", "delete"], permission_classes=[EsEstudiante])
    def seguir(self, request, pk=None):
        """RF-23: el estudiante recibe un aviso cuando la empresa publica una convocatoria."""
        empresa = self.get_object()
        if request.method == "POST":
            EmpresaSeguida.objects.get_or_create(estudiante=self._perfil, empresa=empresa)
        else:
            EmpresaSeguida.objects.filter(estudiante=self._perfil, empresa=empresa).delete()
        return Response(EmpresaPaginaSerializer(self.get_queryset().get(pk=empresa.pk), context=self.get_serializer_context()).data)


class MiEmpresaSerializer(serializers.ModelSerializer):
    """RF-20. La razón social y el NIT son datos legales: los corrige la oficina."""

    logo = serializers.SerializerMethodField()
    estado_nombre = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = Empresa
        fields = ["id", "razon_social", "nit", "estado", "estado_nombre", "sector", "ciudad", "tamano", "descripcion",
                  "sitio_web", "direccion", "contacto_nombre", "contacto_email", "contacto_telefono", "logo"]
        read_only_fields = ["razon_social", "nit", "estado"]

    def get_logo(self, empresa):
        return empresa.logo.url if empresa.logo else None


class LogoSerializer(serializers.Serializer):
    logo = serializers.ImageField(validators=[validar_imagen])


class MiEmpresaView(APIView):
    permission_classes = [EsEmpresa]
    serializer_class = MiEmpresaSerializer

    def get(self, request):
        return Response(MiEmpresaSerializer(request.user.vinculo_empresa.empresa).data)

    def patch(self, request):
        serializer = MiEmpresaSerializer(request.user.vinculo_empresa.empresa, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class MiLogoView(APIView):
    permission_classes = [EsEmpresa]
    parser_classes = [MultiPartParser]
    serializer_class = LogoSerializer

    def post(self, request):
        datos = LogoSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        empresa = request.user.vinculo_empresa.empresa
        anterior = empresa.logo.name if empresa.logo else None
        logo = datos.validated_data["logo"]
        empresa.logo.save(logo.name, logo, save=True)  # RutaAleatoria pone un nombre UUID y conserva la extensión
        if anterior:
            empresa.logo.storage.delete(anterior)
        return Response(MiEmpresaSerializer(empresa).data, status=status.HTTP_201_CREATED)
