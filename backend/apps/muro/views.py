"""Muro de publicaciones (M10). Las reglas de quién publica y qué se ve están en servicios.py."""

from django.db.models import Count, Exists, OuterRef, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.comun.errores import ErrorRegla
from apps.comun.permisos import EsOficina
from apps.cuentas.models import Rol

from . import servicios
from .models import PublicacionGuardada, Reaccion
from .serializers import ComentarioSerializer, PublicacionEntradaSerializer, PublicacionSerializer


class PublicacionViewSet(viewsets.ModelViewSet):
    serializer_class = PublicacionSerializer

    def get_queryset(self):
        usuario = self.request.user
        consulta = (
            servicios.visibles(usuario)
            .select_related("autor", "empresa", "convocatoria")
            .prefetch_related("programas")
            .annotate(
                reacciones_total=Count("reacciones", distinct=True),
                comentarios_total=Count("comentarios", filter=Q(comentarios__oculto=False), distinct=True),
                me_interesa=Exists(Reaccion.objects.filter(publicacion=OuterRef("pk"), usuario=usuario)),
                guardada=Exists(PublicacionGuardada.objects.filter(publicacion=OuterRef("pk"), usuario=usuario)),
            )
        )
        parametros = self.request.query_params
        if tipo := parametros.get("tipo"):
            consulta = consulta.filter(tipo__in=tipo.split(","))
        if estado := parametros.get("estado"):
            consulta = consulta.filter(estado__in=estado.split(","))
        if empresa := parametros.get("empresa"):
            consulta = consulta.filter(empresa_id=empresa)
        if parametros.get("guardadas") == "1":
            consulta = consulta.filter(guardada=True)
        if parametros.get("para_mi") == "1" and usuario.rol == Rol.ESTUDIANTE:  # RF-100: lo dirigido a su programa
            consulta = consulta.filter(Q(para_todos_programas=True) | Q(programas=usuario.perfil_estudiante.programa_id))
        if texto := parametros.get("q", "").strip():
            consulta = consulta.filter(Q(titulo__icontains=texto) | Q(texto__icontains=texto) | Q(fuente_externa__icontains=texto))
        return consulta.distinct().order_by("-creado_en", "-pk")

    def _responder(self, publicacion, codigo=status.HTTP_200_OK):
        return Response(self.get_serializer(self.get_queryset().get(pk=publicacion.pk)).data, status=codigo)

    def _entrada(self, parcial=False):
        datos = PublicacionEntradaSerializer(data=self.request.data, partial=parcial)
        datos.is_valid(raise_exception=True)
        valores = dict(datos.validated_data)
        return valores, valores.pop("programas", None)

    def create(self, request):
        if not servicios.tipos_permitidos(request.user):
            raise PermissionDenied("Tu cuenta no puede publicar en el muro.")
        datos, programas = self._entrada()
        if "tipo" not in datos:
            raise ErrorRegla("Indica el tipo de publicación.")
        return self._responder(servicios.crear(request.user, datos, programas or []), status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """PUT y PATCH se tratan igual: solo se cambian los campos enviados. El tipo no cambia al editar."""
        datos, programas = self._entrada(parcial=True)
        datos.pop("tipo", None)
        return self._responder(servicios.editar(self.get_object(), request.user, datos, programas))

    def destroy(self, request, pk=None):
        servicios.eliminar(self.get_object(), request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False)
    def permisos(self, request):
        """Qué tipos puede publicar el usuario: el frontend decide si muestra el formulario."""
        return Response({"tipos": sorted(servicios.tipos_permitidos(request.user))})

    @action(detail=True, methods=["post"], permission_classes=[EsOficina])
    def ocultar(self, request, pk=None):
        return self._responder(servicios.ocultar(self.get_object(), request.user, request.data.get("motivo", "")))

    @action(detail=True, methods=["post"], permission_classes=[EsOficina])
    def mostrar(self, request, pk=None):
        return self._responder(servicios.mostrar(self.get_object(), request.user))

    @action(detail=True, methods=["post"])
    def reaccionar(self, request, pk=None):
        servicios.alternar_reaccion(self.get_object(), request.user)
        return self._responder(self.get_object())

    @action(detail=True, methods=["post"])
    def guardar(self, request, pk=None):
        servicios.alternar_guardada(self.get_object(), request.user)
        return self._responder(self.get_object())

    @action(detail=True, methods=["get", "post"])
    def comentarios(self, request, pk=None):
        publicacion = self.get_object()
        if request.method == "POST":
            servicios.comentar(publicacion, request.user, request.data.get("texto", ""))
        comentarios = publicacion.comentarios.select_related("autor")
        if not servicios.es_oficina(request.user):
            comentarios = comentarios.filter(oculto=False)
        return Response(ComentarioSerializer(comentarios, many=True).data)

    @action(detail=True, methods=["post"], permission_classes=[EsOficina], url_path=r"comentarios/(?P<comentario_id>\d+)/ocultar")
    def ocultar_comentario(self, request, pk=None, comentario_id=None):
        comentario = get_object_or_404(self.get_object().comentarios, pk=comentario_id)
        servicios.ocultar_comentario(comentario, request.user)
        return Response(ComentarioSerializer(comentario).data)
