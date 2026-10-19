"""Convocatorias (M4, M5). Cada rol ve un conjunto distinto (RF-07) y los cambios de estado pasan por servicios.py."""

from functools import cached_property

from django.contrib.postgres.search import SearchQuery
from django.db.models import Count, Q
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.cuentas.models import Rol
from apps.postulaciones import servicios as servicios_postulacion
from apps.postulaciones.models import Postulacion

from . import afinidad, servicios
from .models import Convocatoria, ConvocatoriaGuardada
from .serializers import ConvocatoriaSerializer

ACCIONES_ESTUDIANTE = {"list", "retrieve", "resumen", "recomendadas", "guardar"}
SOLO_ESTUDIANTE = {"recomendadas", "guardar"}
MAX_RECOMENDADAS = 6


class ObservacionSerializer(serializers.Serializer):
    observacion = serializers.CharField(required=False, allow_blank=True, default="")


class ConvocatoriaViewSet(viewsets.ModelViewSet):
    serializer_class = ConvocatoriaSerializer

    @property
    def _es_estudiante(self):
        return self.request.user.rol == Rol.ESTUDIANTE

    @cached_property
    def _perfil(self):
        return self.request.user.perfil_estudiante

    def _base(self, con_conteo=True):
        """Lo que cada rol puede ver. Un recurso ajeno responde 404 (RNF-05)."""
        usuario = self.request.user
        consulta = Convocatoria.objects.select_related("empresa", "ciudad", "creada_por").prefetch_related(
            "programas", "habilidades", "empresa__convenios"
        )
        if self._es_estudiante:
            return consulta.filter(estado=Convocatoria.Estado.PUBLICADA)
        if con_conteo:
            consulta = consulta.annotate(num_postulaciones=Count("postulaciones"))
        if usuario.rol == Rol.EMPRESA:
            vinculo = getattr(usuario, "vinculo_empresa", None)
            return consulta.filter(empresa=vinculo.empresa) if vinculo else consulta.none()
        return consulta

    def get_queryset(self):
        consulta = self._base()
        parametros = self.request.query_params
        if estado := parametros.get("estado"):
            consulta = consulta.filter(estado__in=estado.split(","))
        if empresa := parametros.get("empresa"):
            consulta = consulta.filter(empresa_id=empresa)
        for filtro in ("modalidad", "tipo_vinculacion", "ciudad"):
            if valor := parametros.get(filtro):
                consulta = consulta.filter(**{filtro: valor})
        if parametros.get("con_apoyo") == "1":
            consulta = consulta.filter(apoyo_economico__gt=0)
        if self._es_estudiante:
            if parametros.get("mi_programa") == "1":  # RF-40: vista por defecto del estudiante
                consulta = consulta.filter(programas=self._perfil.programa_id)
            if parametros.get("guardadas") == "1":
                consulta = consulta.filter(convocatoriaguardada__estudiante=self._perfil)
        if texto := parametros.get("q", "").strip():
            coincide = Q(titulo__icontains=texto) | Q(empresa__razon_social__icontains=texto)
            if self._es_estudiante:  # Búsqueda de texto completo en español (arquitectura 3.6)
                coincide |= Q(search_vector=SearchQuery(texto, config="spanish", search_type="websearch"))
            consulta = consulta.filter(coincide)
        orden = "-publicada_en" if self._es_estudiante else "-actualizado_en"
        return consulta.distinct().order_by(orden, "-pk")

    def get_serializer_context(self):
        contexto = super().get_serializer_context()
        if self._es_estudiante:
            perfil = self._perfil
            contexto["estudiante"] = {
                "perfil": perfil,
                "habilidades": set(perfil.habilidades.values_list("id", flat=True)),
                "postulaciones": {p.convocatoria_id: p for p in Postulacion.objects.filter(estudiante=perfil)},
                "guardadas": set(ConvocatoriaGuardada.objects.filter(estudiante=perfil).values_list("convocatoria_id", flat=True)),
                "motivo_perfil": servicios_postulacion.motivo_perfil(perfil),
            }
        return contexto

    def check_permissions(self, request):
        super().check_permissions(request)
        if request.user.rol == Rol.ESTUDIANTE and self.action not in ACCIONES_ESTUDIANTE:
            raise PermissionDenied("Los estudiantes no pueden modificar convocatorias.")
        if request.user.rol != Rol.ESTUDIANTE and self.action in SOLO_ESTUDIANTE:
            raise PermissionDenied("Esta opción es solo para estudiantes.")

    def create(self, request, *args, **kwargs):
        if request.user.rol == Rol.EMPRESA and not request.user.vinculo_empresa.empresa.puede_publicar:
            raise PermissionDenied("Tu empresa debe ser aliada y tener un convenio vigente para crear convocatorias (RN-02).")
        return super().create(request, *args, **kwargs)

    def perform_update(self, serializer):
        convocatoria = serializer.instance
        if "editar" not in servicios.acciones_permitidas(convocatoria, self.request.user):
            raise PermissionDenied(f"No se puede editar una convocatoria en estado «{convocatoria.get_estado_display()}».")
        estado_anterior = convocatoria.estado
        servicios.despues_de_editar(serializer.save(), self.request.user, estado_anterior)

    def perform_destroy(self, instancia):
        servicios.eliminar(instancia, self.request.user)

    def _responder(self, convocatoria, codigo=status.HTTP_200_OK):
        convocatoria = self._base().get(pk=convocatoria.pk)
        return Response(self.get_serializer(convocatoria).data, status=codigo)

    @action(detail=False)
    def resumen(self, request):
        conteos = dict(self._base(con_conteo=False).order_by().values_list("estado").annotate(total=Count("id")))
        return Response({estado: conteos.get(estado, 0) for estado in Convocatoria.Estado.values})

    @action(detail=False)
    def recomendadas(self, request):
        """RF-42: convocatorias de su programa a las que no se ha postulado, ordenadas por afinidad."""
        contexto = self.get_serializer_context()["estudiante"]
        candidatas = (
            self._base().filter(programas=self._perfil.programa_id)
            .exclude(pk__in=contexto["postulaciones"].keys()).order_by("-publicada_en")[:100]
        )
        ordenadas = sorted(
            candidatas, key=lambda c: afinidad.calcular(self._perfil, c, contexto["habilidades"])["total"], reverse=True
        )[:MAX_RECOMENDADAS]
        return Response(self.get_serializer(ordenadas, many=True).data)

    @action(detail=True, methods=["post", "delete"])
    def guardar(self, request, pk=None):
        """RF-44: guardar o quitar de guardadas."""
        convocatoria = self.get_object()
        if request.method == "POST":
            ConvocatoriaGuardada.objects.get_or_create(estudiante=self._perfil, convocatoria=convocatoria)
        else:
            ConvocatoriaGuardada.objects.filter(estudiante=self._perfil, convocatoria=convocatoria).delete()
        return self._responder(convocatoria)

    @action(detail=True, methods=["post"], url_path="enviar-revision")
    def enviar_revision(self, request, pk=None):
        return self._responder(servicios.enviar_revision(self.get_object(), request.user))

    @action(detail=True, methods=["post"])
    def aprobar(self, request, pk=None):
        return self._responder(servicios.aprobar(self.get_object(), request.user))

    @action(detail=True, methods=["post"])
    def devolver(self, request, pk=None):
        datos = ObservacionSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        return self._responder(servicios.devolver(self.get_object(), request.user, datos.validated_data["observacion"]))

    @action(detail=True, methods=["post"])
    def cerrar(self, request, pk=None):
        return self._responder(servicios.cerrar(self.get_object(), request.user))

    @action(detail=True, methods=["post"])
    def duplicar(self, request, pk=None):
        return self._responder(servicios.duplicar(self.get_object(), request.user), status.HTTP_201_CREATED)
