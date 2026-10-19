"""Endpoints del estudiante sobre su propio perfil (M2): /api/v1/estudiantes/yo/..."""

from django.db import IntegrityError, transaction
from rest_framework import serializers, status, viewsets
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comun.archivos import respuesta_protegida, validar_pdf
from apps.comun.errores import ErrorRegla
from apps.comun.permisos import EsEstudiante

from . import servicios
from .models import Certificacion, Enlace, Experiencia, IdiomaEstudiante, PerfilEstudiante, Proyecto
from .serializers import (
    CertificacionSerializer, EnlaceSerializer, ExperienciaSerializer, HabilidadesSerializer, IdiomaSerializer,
    PerfilPropioSerializer, ProyectoSerializer,
)


def perfil_de(request):
    return (
        PerfilEstudiante.objects.select_related("usuario", "programa", "ciudad")
        .prefetch_related("estudiantehabilidad_set__habilidad", "idiomas", "experiencias", "proyectos", "certificaciones", "enlaces")
        .get(usuario=request.user)
    )


class MiPerfilView(APIView):
    permission_classes = [EsEstudiante]
    serializer_class = PerfilPropioSerializer

    def get(self, request):
        return Response(PerfilPropioSerializer(perfil_de(request)).data)

    def patch(self, request):
        serializer = PerfilPropioSerializer(perfil_de(request), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(PerfilPropioSerializer(perfil_de(request)).data)


class MisHabilidadesView(APIView):
    """PUT con la lista completa de habilidades: reemplaza las anteriores (RF-11)."""

    permission_classes = [EsEstudiante]
    serializer_class = HabilidadesSerializer

    def put(self, request):
        serializer = HabilidadesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        servicios.reemplazar_habilidades(perfil_de(request), serializer.validated_data["habilidades"])
        return Response(PerfilPropioSerializer(perfil_de(request)).data)


class HojaVidaSerializer(serializers.Serializer):
    archivo = serializers.FileField(validators=[validar_pdf])


class MiHojaVidaView(APIView):
    """RF-13: subir, ver y borrar la hoja de vida (PDF protegido)."""

    permission_classes = [EsEstudiante]
    parser_classes = [MultiPartParser]
    serializer_class = HojaVidaSerializer

    def get(self, request):
        perfil = perfil_de(request)
        return respuesta_protegida(perfil.hoja_vida, f"hoja-de-vida-{perfil.usuario.apellidos}.pdf")

    def post(self, request):
        serializer = HojaVidaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        servicios.guardar_hoja_vida(perfil_de(request), serializer.validated_data["archivo"])
        return Response(PerfilPropioSerializer(perfil_de(request)).data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        servicios.borrar_hoja_vida(perfil_de(request))
        return Response(PerfilPropioSerializer(perfil_de(request)).data)


class _SeccionPerfil(viewsets.ModelViewSet):
    """CRUD de una sección del perfil (idiomas, experiencias, ...) limitado al estudiante autenticado."""

    permission_classes = [EsEstudiante]
    pagination_class = None
    modelo = None

    def get_queryset(self):
        return self.modelo.objects.filter(estudiante__usuario=self.request.user)

    def _guardar(self, serializer, **extra):
        try:
            with transaction.atomic():  # Punto de guardado: el error no invalida la transacción de la petición
                serializer.save(**extra)
        except IntegrityError:
            raise ErrorRegla("Ese registro ya existe en tu perfil.")

    def perform_create(self, serializer):
        self._guardar(serializer, estudiante=self.request.user.perfil_estudiante)

    def perform_update(self, serializer):
        self._guardar(serializer)


class MisIdiomasViewSet(_SeccionPerfil):
    modelo, serializer_class = IdiomaEstudiante, IdiomaSerializer


class MisExperienciasViewSet(_SeccionPerfil):
    modelo, serializer_class = Experiencia, ExperienciaSerializer


class MisProyectosViewSet(_SeccionPerfil):
    modelo, serializer_class = Proyecto, ProyectoSerializer


class MisCertificacionesViewSet(_SeccionPerfil):
    modelo, serializer_class = Certificacion, CertificacionSerializer


class MisEnlacesViewSet(_SeccionPerfil):
    modelo, serializer_class = Enlace, EnlaceSerializer
