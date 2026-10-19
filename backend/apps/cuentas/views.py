from django.core.cache import cache
from rest_framework import generics, status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from . import servicios
from .serializers import (
    InicioSesionSerializer, RegistroEmpresaSerializer, RegistroEstudianteSerializer, UsuarioActualSerializer,
    VerificarCorreoSerializer,
)


def _ip(request):
    return request.META.get("HTTP_X_REAL_IP") or request.META.get("REMOTE_ADDR")


class InicioSesionView(TokenObtainPairView):
    """RNF-07: máximo 5 intentos fallidos por minuto para cada combinación de IP y correo."""

    serializer_class = InicioSesionSerializer
    MAX_FALLIDOS = 5
    VENTANA_SEGUNDOS = 60

    def post(self, request, *args, **kwargs):
        clave = f"login-fallido:{_ip(request)}:{str(request.data.get('email', '')).lower()}"
        if cache.get(clave, 0) >= self.MAX_FALLIDOS:
            return Response(
                {"detail": "Demasiados intentos fallidos. Espera un minuto e inténtalo de nuevo."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        try:
            return super().post(request, *args, **kwargs)
        except AuthenticationFailed:
            cache.add(clave, 0, self.VENTANA_SEGUNDOS)
            cache.incr(clave)
            raise


class _RegistroView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "registro"
    serializer_class = None
    servicio = None
    mensaje = ""

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        datos = dict(serializer.validated_data)
        datos.pop("acepta_politica")
        type(self).servicio(**datos, ip=_ip(request))
        return Response({"detalle": self.mensaje}, status=status.HTTP_201_CREATED)


class RegistroEstudianteView(_RegistroView):
    serializer_class = RegistroEstudianteSerializer
    servicio = staticmethod(servicios.registrar_estudiante)
    mensaje = "Cuenta creada. Revisa tu correo institucional para activarla."


class RegistroEmpresaView(_RegistroView):
    serializer_class = RegistroEmpresaSerializer
    servicio = staticmethod(servicios.registrar_empresa)
    mensaje = "Solicitud enviada. Confirma tu correo; la oficina de prácticas revisará tu empresa."


class VerificarCorreoView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = VerificarCorreoSerializer

    def post(self, request):
        serializer = VerificarCorreoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        servicios.verificar_correo(serializer.validated_data["token"])
        return Response({"detalle": "Correo verificado. Ya puedes iniciar sesión."})


class YoView(generics.RetrieveAPIView):
    serializer_class = UsuarioActualSerializer

    def get_object(self):
        return self.request.user


class RecuperarClaveView(APIView):
    """RF-05: envía el enlace de recuperación. La respuesta no revela si el correo existe."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "registro"

    def post(self, request):
        servicios.solicitar_recuperacion(str(request.data.get("email", "")))
        return Response({"detalle": "Si el correo está registrado, te enviamos un enlace para restablecer la contraseña."})


class RestablecerClaveView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        servicios.restablecer_clave(str(request.data.get("uid", "")), str(request.data.get("token", "")), str(request.data.get("password", "")))
        return Response({"detalle": "Contraseña actualizada. Ya puedes iniciar sesión."})


class CambiarClaveView(APIView):
    def post(self, request):
        servicios.cambiar_clave(request.user, str(request.data.get("actual", "")), str(request.data.get("password", "")))
        return Response({"detalle": "Contraseña actualizada."})
