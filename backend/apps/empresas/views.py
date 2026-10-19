"""Gestión de empresas aliadas y convenios por parte de la oficina de prácticas (M3, RF-24, RF-25, RF-60)."""

from django.db.models import Count, Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.comun.archivos import respuesta_protegida
from apps.comun.permisos import EsOficina

from . import servicios
from .models import Convenio, Empresa
from .serializers import (
    CrearEmpresaSerializer, DatosConvenioSerializer, EmpresaDetalleSerializer, EmpresaListaSerializer,
    MotivoSerializer,
)

CAMPOS_CONVENIO = ("numero", "fecha_inicio", "fecha_fin", "documento")


def _separar_convenio(datos):
    return {c: datos.pop(c) for c in CAMPOS_CONVENIO if c in datos}


class EmpresasOficinaViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [EsOficina]

    def get_queryset(self):
        consulta = Empresa.objects.select_related("sector", "ciudad").prefetch_related("convenios")
        parametros = self.request.query_params
        if estado := parametros.get("estado"):
            consulta = consulta.filter(estado__in=estado.split(","))
        if texto := parametros.get("q"):
            consulta = consulta.filter(Q(razon_social__icontains=texto) | Q(nit__icontains=texto))
        return consulta

    def get_serializer_class(self):
        return EmpresaDetalleSerializer if self.action == "retrieve" else EmpresaListaSerializer

    def _responder(self, empresa, codigo=status.HTTP_200_OK):
        empresa = self.get_queryset().get(pk=empresa.pk)  # Recarga con los convenios actualizados
        return Response(EmpresaDetalleSerializer(empresa).data, status=codigo)

    def create(self, request):
        serializer = CrearEmpresaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = dict(serializer.validated_data)
        convenio = _separar_convenio(datos)
        empresa = servicios.crear_por_oficina(request.user, convenio, **datos)
        return self._responder(empresa, status.HTTP_201_CREATED)

    @action(detail=False)
    def resumen(self, request):
        conteos = dict(Empresa.objects.values_list("estado").annotate(total=Count("id")))
        return Response({estado: conteos.get(estado, 0) for estado in Empresa.Estado.values})

    @action(detail=True, methods=["post"])
    def aprobar(self, request, pk=None):
        serializer = DatosConvenioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._responder(servicios.aprobar(self.get_object(), request.user, **serializer.validated_data))

    @action(detail=True, methods=["post"])
    def rechazar(self, request, pk=None):
        motivo = MotivoSerializer(data=request.data)
        motivo.is_valid(raise_exception=True)
        return self._responder(servicios.rechazar(self.get_object(), request.user, motivo.validated_data["motivo"]))

    @action(detail=True, methods=["post"])
    def suspender(self, request, pk=None):
        motivo = MotivoSerializer(data=request.data)
        motivo.is_valid(raise_exception=True)
        return self._responder(servicios.suspender(self.get_object(), request.user, motivo.validated_data["motivo"]))

    @action(detail=True, methods=["post"])
    def reactivar(self, request, pk=None):
        return self._responder(servicios.reactivar(self.get_object(), request.user))

    @action(detail=True, methods=["post"])
    def convenios(self, request, pk=None):
        serializer = DatosConvenioSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        empresa = self.get_object()
        servicios.registrar_convenio(empresa, request.user, **serializer.validated_data)
        return self._responder(empresa, status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path=r"convenios/(?P<convenio_id>\d+)/documento")
    def documento_convenio(self, request, pk=None, convenio_id=None):
        convenio = get_object_or_404(Convenio, pk=convenio_id, empresa_id=pk)
        return respuesta_protegida(convenio.documento, f"convenio-{convenio.numero}.pdf")

