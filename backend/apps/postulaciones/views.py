"""Postulaciones (M6). Cada rol ve solo las suyas (RN-10, RNF-05) y todo cambio pasa por servicios.py."""

from django.db.models import Count, Prefetch, Q
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.comun.archivos import respuesta_protegida
from apps.cuentas.models import Rol

from apps.comun.permisos import EsOficina

from . import practicas, servicios
from .models import EntradaSeguimiento, EstadoPostulacion, Postulacion, Practica
from .serializers import (
    CambioEstadoSerializer, CrearPostulacionSerializer, EntradaNuevaSerializer, EntrevistaSerializer, LegalizarSerializer,
    PostulacionDetalleSerializer, PostulacionListaSerializer, PracticaSerializer, SeguimientoSerializer, VerificarSerializer,
)


class PostulacionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):

    def _base(self):
        usuario = self.request.user
        consulta = Postulacion.objects.select_related(
            "convocatoria__empresa", "estudiante__usuario", "estudiante__programa"
        ).prefetch_related("entrevistas")
        if usuario.rol == Rol.ESTUDIANTE:
            return consulta.filter(estudiante__usuario=usuario)
        if usuario.rol == Rol.EMPRESA:
            vinculo = getattr(usuario, "vinculo_empresa", None)
            return consulta.filter(convocatoria__empresa=vinculo.empresa) if vinculo else consulta.none()
        return consulta

    def get_queryset(self):
        consulta = self._base()
        if self.action == "retrieve":
            consulta = consulta.prefetch_related(
                "historial__usuario", Prefetch("seguimiento", queryset=EntradaSeguimiento.objects.select_related("autor")),
                "convocatoria__programas", "convocatoria__habilidades", "estudiante__habilidades",
            )
        parametros = self.request.query_params
        if estado := parametros.get("estado"):
            consulta = consulta.filter(estado__in=estado.split(","))
        for filtro, campo in (("convocatoria", "convocatoria_id"), ("empresa", "convocatoria__empresa_id"), ("programa", "estudiante__programa_id")):
            if valor := parametros.get(filtro):
                consulta = consulta.filter(**{campo: valor})
        if texto := parametros.get("q", "").strip():
            consulta = consulta.filter(
                Q(estudiante__usuario__nombres__icontains=texto) | Q(estudiante__usuario__apellidos__icontains=texto)
                | Q(estudiante__usuario__email__icontains=texto) | Q(convocatoria__titulo__icontains=texto)
            )
        orden = parametros.get("orden")
        return consulta.order_by("-afinidad", "-creado_en") if orden == "afinidad" else consulta.order_by("-actualizado_en")

    def get_serializer_class(self):
        if self.action == "create":
            return CrearPostulacionSerializer
        return PostulacionDetalleSerializer if self.action == "retrieve" else PostulacionListaSerializer

    def _detalle(self, postulacion, codigo=status.HTTP_200_OK):
        self.action = "retrieve"
        postulacion = self.get_queryset().get(pk=postulacion.pk)
        return Response(PostulacionDetalleSerializer(postulacion, context=self.get_serializer_context()).data, status=codigo)

    def create(self, request):
        """RF-50: solo el estudiante se postula; las reglas RN-04 a RN-08 se validan en el servicio."""
        if request.user.rol != Rol.ESTUDIANTE:
            raise PermissionDenied("Solo los estudiantes se postulan.")
        datos = CrearPostulacionSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        postulacion = servicios.postular(
            request.user.perfil_estudiante, datos.validated_data["convocatoria"], datos.validated_data["mensaje_presentacion"]
        )
        return self._detalle(postulacion, status.HTTP_201_CREATED)

    @action(detail=False)
    def resumen(self, request):
        base = self._base()
        if convocatoria := request.query_params.get("convocatoria"):
            base = base.filter(convocatoria_id=convocatoria)
        conteos = dict(base.order_by().values_list("estado").annotate(total=Count("id")))
        return Response({estado: conteos.get(estado, 0) for estado in EstadoPostulacion.values})

    @action(detail=True, methods=["post"], url_path="cambiar-estado")
    def cambiar_estado(self, request, pk=None):
        datos = CambioEstadoSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        d = datos.validated_data
        return self._detalle(servicios.cambiar_estado(self.get_object(), d["estado"], request.user, d["comentario"], d["motivo"]))

    @action(detail=True, methods=["post"])
    def retirar(self, request, pk=None):
        comentario = request.data.get("comentario", "")
        return self._detalle(servicios.retirar(self.get_object(), request.user, comentario))

    @action(detail=True, methods=["post"])
    def entrevistas(self, request, pk=None):
        datos = EntrevistaSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        servicios.programar_entrevista(self.get_object(), request.user, **datos.validated_data)
        return self._detalle(self.get_object(), status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def seguimiento(self, request, pk=None):
        datos = EntradaNuevaSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        entrada = servicios.agregar_seguimiento(self.get_object(), request.user, **datos.validated_data)
        return Response(SeguimientoSerializer(entrada).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="hoja-vida")
    def hoja_vida(self, request, pk=None):
        """RN-10: la copia de la HV solo la ven el estudiante, la empresa de la convocatoria y la oficina (por el queryset)."""
        postulacion = self.get_object()
        return respuesta_protegida(postulacion.hoja_vida, f"hv-{postulacion.estudiante.usuario.apellidos}-{postulacion.pk}.pdf")

    @action(detail=True, methods=["post"], permission_classes=[EsOficina])
    def verificar(self, request, pk=None):
        """RF-62a: la oficina registra la verificación en persona de los requisitos del seleccionado."""
        datos = VerificarSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        practicas.verificar(self.get_object(), request.user, **datos.validated_data)
        return self._detalle(self.get_object())

    @action(detail=True, methods=["post"], permission_classes=[EsOficina])
    def legalizar(self, request, pk=None):
        """RF-64: crea la práctica, ubica al estudiante y cierra sus otras postulaciones (RN-07, RN-08, RN-09)."""
        datos = LegalizarSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        practicas.legalizar(self.get_object(), request.user, **datos.validated_data)
        return self._detalle(self.get_object(), status.HTTP_201_CREATED)


class PracticaViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Prácticas legalizadas (RF-64, RF-65). La oficina las gestiona; el estudiante y la empresa ven las suyas."""

    serializer_class = PracticaSerializer

    def get_queryset(self):
        consulta = practicas.practicas_de(self.request.user)
        parametros = self.request.query_params
        if estado := parametros.get("estado"):
            consulta = consulta.filter(estado__in=estado.split(","))
        if texto := parametros.get("q", "").strip():
            consulta = consulta.filter(
                Q(estudiante__usuario__nombres__icontains=texto) | Q(estudiante__usuario__apellidos__icontains=texto)
                | Q(postulacion__convocatoria__empresa__razon_social__icontains=texto)
            )
        return consulta.order_by("-legalizada_en")

    @action(detail=False)
    def resumen(self, request):
        conteos = dict(practicas.practicas_de(request.user).order_by().values_list("estado").annotate(total=Count("id")))
        return Response({estado: conteos.get(estado, 0) for estado in Practica.Estado.values})

    def _texto(self, request):
        return str(request.data.get("observacion", ""))

    @action(detail=True, methods=["post"], permission_classes=[EsOficina])
    def finalizar(self, request, pk=None):
        return Response(PracticaSerializer(practicas.finalizar(self.get_object(), request.user, self._texto(request))).data)

    @action(detail=True, methods=["post"], permission_classes=[EsOficina])
    def cancelar(self, request, pk=None):
        return Response(PracticaSerializer(practicas.cancelar(self.get_object(), request.user, self._texto(request))).data)

    @action(detail=True, methods=["get"])
    def documento(self, request, pk=None):
        practica = self.get_object()
        return respuesta_protegida(practica.documento_soporte, f"soporte-practica-{practica.pk}.pdf")

