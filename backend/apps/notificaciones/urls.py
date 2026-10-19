from django.urls import path

from . import views

urlpatterns = [
    path("", views.NotificacionesView.as_view(), name="notificaciones"),
    path("no-leidas/conteo/", views.conteo_no_leidas, name="notificaciones-conteo"),
    path("leer-todas/", views.marcar_todas_leidas, name="notificaciones-leer-todas"),
    path("<int:pk>/leer/", views.marcar_leida, name="notificacion-leer"),
]
