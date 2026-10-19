from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import SimpleRouter

from apps.convocatorias.views import ConvocatoriaViewSet
from apps.empresas import vistas_publicas
from apps.empresas.views import EmpresasOficinaViewSet
from apps.estudiantes import vistas_perfil
from apps.estudiantes.views import EstudiantesOficinaViewSet
from apps.estudiantes.vistas_talento import TalentoViewSet
from apps.muro.views import PublicacionViewSet
from apps.postulaciones.views import PostulacionViewSet, PracticaViewSet
from apps.reportes.views import AlertasView, ExportarView, IndicadoresView, ResumenEmpresaView

admin.site.site_header = "PB Conecta · Administración"
admin.site.site_title = "PB Conecta"
admin.site.index_title = "Panel del superadministrador"

router = SimpleRouter()
router.register("convocatorias", ConvocatoriaViewSet, basename="convocatoria")
router.register("oficina/empresas", EmpresasOficinaViewSet, basename="oficina-empresa")
router.register("oficina/estudiantes", EstudiantesOficinaViewSet, basename="oficina-estudiante")
router.register("postulaciones", PostulacionViewSet, basename="postulacion")
router.register("practicas", PracticaViewSet, basename="practica")
router.register("muro/publicaciones", PublicacionViewSet, basename="publicacion")
router.register("empresas", vistas_publicas.EmpresasPublicasViewSet, basename="empresa")
router.register("talento", TalentoViewSet, basename="talento")
router.register("estudiantes/yo/idiomas", vistas_perfil.MisIdiomasViewSet, basename="mis-idiomas")
router.register("estudiantes/yo/experiencias", vistas_perfil.MisExperienciasViewSet, basename="mis-experiencias")
router.register("estudiantes/yo/proyectos", vistas_perfil.MisProyectosViewSet, basename="mis-proyectos")
router.register("estudiantes/yo/certificaciones", vistas_perfil.MisCertificacionesViewSet, basename="mis-certificaciones")
router.register("estudiantes/yo/enlaces", vistas_perfil.MisEnlacesViewSet, basename="mis-enlaces")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("api/v1/auth/", include("apps.cuentas.urls")),
    path("api/v1/catalogos/", include("apps.catalogos.urls")),
    path("api/v1/notificaciones/", include("apps.notificaciones.urls")),
    path("api/v1/estudiantes/yo/", vistas_perfil.MiPerfilView.as_view(), name="mi-perfil"),
    path("api/v1/estudiantes/yo/habilidades/", vistas_perfil.MisHabilidadesView.as_view(), name="mis-habilidades"),
    path("api/v1/estudiantes/yo/hoja-vida/", vistas_perfil.MiHojaVidaView.as_view(), name="mi-hoja-vida"),
    path("api/v1/oficina/alertas/", AlertasView.as_view(), name="alertas"),
    path("api/v1/oficina/indicadores/", IndicadoresView.as_view(), name="indicadores"),
    path("api/v1/oficina/exportar/<slug:reporte>.csv", ExportarView.as_view(), name="exportar"),
    path("api/v1/empresas/yo/resumen/", ResumenEmpresaView.as_view(), name="resumen-empresa"),
    path("api/v1/empresas/yo/", vistas_publicas.MiEmpresaView.as_view(), name="mi-empresa"),
    path("api/v1/empresas/yo/logo/", vistas_publicas.MiLogoView.as_view(), name="mi-logo"),
    path("api/v1/", include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
