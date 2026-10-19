"""Gestión de estudiantes y habilitación por la oficina de prácticas (M7)."""

from django.db.models import Count, Prefetch, Q
from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.comun.permisos import EsOficina

from . import servicios
from .models import EstadoEstudiante, Habilitacion, NotaAsesoria, PerfilEstudiante


class HabilitacionSerializer(serializers.ModelSerializer):
    periodo = serializers.CharField(source="periodo.codigo")
    funcionario = serializers.CharField(source="funcionario.nombre_completo")
    accion_nombre = serializers.CharField(source="get_accion_display")

    class Meta:
        model = Habilitacion
        fields = ["id", "accion", "accion_nombre", "periodo", "funcionario", "observacion", "creado_en"]


class EstudianteOficinaSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(source="usuario.nombre_completo")
    email = serializers.CharField(source="usuario.email")
    telefono = serializers.CharField(source="usuario.telefono")
    correo_verificado = serializers.BooleanField(source="usuario.is_active")
    programa_nombre = serializers.CharField(source="programa.nombre")
    estado_nombre = serializers.CharField(source="get_estado_display")
    ultima_habilitacion = serializers.SerializerMethodField()

    class Meta:
        model = PerfilEstudiante
        fields = [
            "id", "nombre", "email", "telefono", "correo_verificado", "programa", "programa_nombre", "semestre",
            "estado", "estado_nombre", "ultima_habilitacion",
        ]

    def get_ultima_habilitacion(self, perfil):
        historial = perfil.habilitaciones.all()  # Prefetch ordenado por -creado_en
        return HabilitacionSerializer(historial[0]).data if historial else None


class EstudianteOficinaDetalleSerializer(EstudianteOficinaSerializer):
    historial = HabilitacionSerializer(source="habilitaciones", many=True)

    class Meta(EstudianteOficinaSerializer.Meta):
        fields = EstudianteOficinaSerializer.Meta.fields + ["historial"]


class NotaAsesoriaSerializer(serializers.ModelSerializer):
    autor = serializers.CharField(source="autor.nombre_completo", read_only=True)

    class Meta:
        model = NotaAsesoria
        fields = ["id", "texto", "autor", "creado_en"]


class ObservacionSerializer(serializers.Serializer):
    observacion = serializers.CharField(required=False, allow_blank=True, default="")


class HabilitarVariosSerializer(ObservacionSerializer):
    ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False, max_length=200)


class EstudiantesOficinaViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [EsOficina]

    def get_queryset(self):
        consulta = PerfilEstudiante.objects.select_related("usuario", "programa").prefetch_related(
            Prefetch("habilitaciones", queryset=Habilitacion.objects.select_related("periodo", "funcionario").order_by("-creado_en"))
        ).order_by("usuario__apellidos", "usuario__nombres")
        parametros = self.request.query_params
        if estado := parametros.get("estado"):
            consulta = consulta.filter(estado__in=estado.split(","))
        if programa := parametros.get("programa"):
            consulta = consulta.filter(programa_id=programa)
        if texto := parametros.get("q"):
            consulta = consulta.filter(
                Q(usuario__nombres__icontains=texto) | Q(usuario__apellidos__icontains=texto)
                | Q(usuario__email__icontains=texto) | Q(documento__icontains=texto)
            )
        return consulta

    def get_serializer_class(self):
        return EstudianteOficinaDetalleSerializer if self.action == "retrieve" else EstudianteOficinaSerializer

    def _responder(self, perfil):
        return Response(EstudianteOficinaDetalleSerializer(self.get_queryset().get(pk=perfil.pk)).data)

    @action(detail=False)
    def resumen(self, request):
        conteos = dict(PerfilEstudiante.objects.values_list("estado").annotate(total=Count("id")))
        return Response({estado: conteos.get(estado, 0) for estado in EstadoEstudiante.values})

    @action(detail=True, methods=["post"])
    def habilitar(self, request, pk=None):
        datos = ObservacionSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        return self._responder(servicios.habilitar(self.get_object(), request.user, datos.validated_data["observacion"]))

    @action(detail=True, methods=["post"])
    def deshabilitar(self, request, pk=None):
        datos = ObservacionSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        return self._responder(servicios.deshabilitar(self.get_object(), request.user, datos.validated_data["observacion"]))

    @action(detail=False, methods=["post"], url_path="habilitar-varios")
    def habilitar_varios(self, request):
        datos = HabilitarVariosSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        return Response(servicios.habilitar_varios(datos.validated_data["ids"], request.user, datos.validated_data["observacion"]))

    @action(detail=True, methods=["get", "post"])
    def notas(self, request, pk=None):
        """RF-67: notas de asesoría de la oficina sobre el estudiante (no las ven el estudiante ni las empresas)."""
        perfil = self.get_object()
        if request.method == "POST":
            nota = NotaAsesoriaSerializer(data=request.data)
            nota.is_valid(raise_exception=True)
            nota.save(estudiante=perfil, autor=request.user)
        notas = perfil.notas_asesoria.select_related("autor")
        return Response(NotaAsesoriaSerializer(notas, many=True).data)

