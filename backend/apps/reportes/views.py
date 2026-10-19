from django.db.models import Count, Q
from django.http import Http404, HttpResponse
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.comun.permisos import EsEmpresa, EsOficina
from apps.convocatorias.models import Convocatoria
from apps.postulaciones.models import EstadoPostulacion as P

from . import alertas, exportaciones, indicadores


class AlertasView(APIView):
    """RF-66: alertas de seguimiento de la oficina, calculadas en el momento."""

    permission_classes = [EsOficina]

    def get(self, request):
        return Response(alertas.calcular())


class IndicadoresView(APIView):
    """RF-80: tablero de indicadores, filtrable por periodo académico y por programa."""

    permission_classes = [EsOficina]

    def get(self, request):
        return Response(indicadores.calcular(request.query_params.get("periodo"), request.query_params.get("programa")))


class ExportarView(APIView):
    """RF-81: descarga de listados en CSV."""

    permission_classes = [EsOficina]

    def get(self, request, reporte):
        if reporte not in exportaciones.REPORTES:
            raise Http404("Reporte no disponible")
        respuesta = HttpResponse(exportaciones.generar(reporte), content_type="text/csv; charset=utf-8")
        nombre = f"pbconecta-{reporte}-{timezone.localdate():%Y%m%d}.csv"
        respuesta["Content-Disposition"] = f'attachment; filename="{nombre}"'
        return respuesta


class ResumenEmpresaView(APIView):
    """RF-82: postulantes por etapa en cada convocatoria de la empresa."""

    permission_classes = [EsEmpresa]

    def get(self, request):
        etapa = lambda *estados: Count("postulaciones", filter=Q(postulaciones__estado__in=estados))  # noqa: E731
        convocatorias = (
            Convocatoria.objects.filter(empresa=request.user.vinculo_empresa.empresa)
            .exclude(estado=Convocatoria.Estado.BORRADOR)
            .annotate(
                total=Count("postulaciones"),
                por_revisar=etapa(P.POSTULADO, P.EN_REVISION),
                en_proceso=etapa(P.PRESELECCIONADO, P.ENTREVISTA),
                seleccionados=etapa(P.SELECCIONADO, P.LEGALIZADO),
            )
            .order_by("-publicada_en", "-creado_en")
        )
        return Response([
            {"id": c.id, "titulo": c.titulo, "estado": c.estado, "estado_nombre": c.get_estado_display(), "cupos": c.cupos,
             "total": c.total, "por_revisar": c.por_revisar, "en_proceso": c.en_proceso, "seleccionados": c.seleccionados}
            for c in convocatorias
        ])
