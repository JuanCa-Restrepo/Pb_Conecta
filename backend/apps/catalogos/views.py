from rest_framework import generics, serializers
from rest_framework.permissions import AllowAny

from .models import Ciudad, Habilidad, PeriodoAcademico, Programa, Sector


class ProgramaSerializer(serializers.ModelSerializer):
    facultad = serializers.CharField(source="facultad.nombre")
    nivel_nombre = serializers.CharField(source="get_nivel_display")

    class Meta:
        model = Programa
        fields = ["id", "nombre", "nivel", "nivel_nombre", "facultad"]


class SectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = ["id", "nombre"]


class CiudadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ciudad
        fields = ["id", "nombre", "departamento"]


class HabilidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Habilidad
        fields = ["id", "nombre", "tipo"]


class PeriodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodoAcademico
        fields = ["id", "codigo", "fecha_inicio", "fecha_fin", "vigente"]


class _CatalogoPublico(generics.ListAPIView):
    """Los catálogos se usan en los formularios de registro, por eso son públicos y sin paginación."""

    permission_classes = [AllowAny]
    authentication_classes = []
    pagination_class = None


class ProgramasView(_CatalogoPublico):
    serializer_class = ProgramaSerializer
    queryset = Programa.objects.filter(activo=True).select_related("facultad")


class SectoresView(_CatalogoPublico):
    serializer_class = SectorSerializer
    queryset = Sector.objects.all()


class CiudadesView(_CatalogoPublico):
    serializer_class = CiudadSerializer
    queryset = Ciudad.objects.all()


class HabilidadesView(generics.ListAPIView):
    serializer_class = HabilidadSerializer
    queryset = Habilidad.objects.all()
    pagination_class = None


class PeriodosView(generics.ListAPIView):
    serializer_class = PeriodoSerializer
    queryset = PeriodoAcademico.objects.all()
    pagination_class = None
