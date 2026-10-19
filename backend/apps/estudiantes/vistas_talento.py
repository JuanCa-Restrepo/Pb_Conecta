"""Endpoints de búsqueda de talento para empresas aliadas (RF-45): /api/v1/talento/."""

from rest_framework import mixins, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.comun.permisos import EsEmpresaAliada
from apps.convocatorias.models import Convocatoria

from . import talento
from .models import PerfilEstudiante
from .serializers import PerfilBase


class TalentoSerializer(PerfilBase):
    """Vista profesional sin correo ni teléfono: el contacto llega con la invitación y la postulación (RF-58)."""

    coincidencias = serializers.IntegerField(read_only=True, default=None)

    class Meta:
        model = PerfilEstudiante
        fields = PerfilBase.CAMPOS + ["coincidencias"]
        read_only_fields = fields


class InvitacionSerializer(serializers.Serializer):
    convocatoria = serializers.PrimaryKeyRelatedField(queryset=Convocatoria.objects.all())
    mensaje = serializers.CharField(required=False, allow_blank=True, default="", max_length=1000)


class TalentoViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [EsEmpresaAliada]  # RN-02: solo empresas aliadas con convenio vigente
    serializer_class = TalentoSerializer

    def get_queryset(self):
        return talento.buscar(self.request.query_params)

    @action(detail=True, methods=["post"])
    def invitar(self, request, pk=None):
        datos = InvitacionSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        talento.invitar(
            request.user.vinculo_empresa.empresa, request.user, self.get_object(),
            datos.validated_data["convocatoria"], datos.validated_data["mensaje"],
        )
        return Response({"detalle": "Invitación enviada. El estudiante la verá en sus notificaciones y por correo."})
