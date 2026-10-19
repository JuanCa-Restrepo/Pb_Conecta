from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path("token/", views.InicioSesionView.as_view(), name="inicio-sesion"),
    path("token/refrescar/", TokenRefreshView.as_view(), name="refrescar-token"),
    path("registro/estudiante/", views.RegistroEstudianteView.as_view(), name="registro-estudiante"),
    path("registro/empresa/", views.RegistroEmpresaView.as_view(), name="registro-empresa"),
    path("verificar-correo/", views.VerificarCorreoView.as_view(), name="verificar-correo"),
    path("yo/", views.YoView.as_view(), name="usuario-actual"),
    path("recuperar/", views.RecuperarClaveView.as_view(), name="recuperar-clave"),
    path("restablecer/", views.RestablecerClaveView.as_view(), name="restablecer-clave"),
    path("cambiar-clave/", views.CambiarClaveView.as_view(), name="cambiar-clave"),
]
