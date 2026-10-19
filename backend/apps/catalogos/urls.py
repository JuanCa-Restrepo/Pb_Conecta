from django.urls import path

from . import views

urlpatterns = [
    path("programas/", views.ProgramasView.as_view(), name="programas"),
    path("sectores/", views.SectoresView.as_view(), name="sectores"),
    path("ciudades/", views.CiudadesView.as_view(), name="ciudades"),
    path("habilidades/", views.HabilidadesView.as_view(), name="habilidades"),
    path("periodos/", views.PeriodosView.as_view(), name="periodos"),
]
