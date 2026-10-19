"""Tablero de indicadores de la oficina (RF-80). Responde la pregunta del proyecto: ¿PB Conecta mejora el acceso a prácticas?

Filtros opcionales:
- `periodo`: cuenta la actividad (habilitaciones, postulaciones, legalizaciones) dentro de las fechas del periodo académico.
- `programa`: limita todo a los estudiantes y convocatorias de ese programa.
"""

from collections import Counter, defaultdict
from datetime import datetime, time

from django.db.models import Count, Min, Q, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from apps.catalogos.models import PeriodoAcademico, Programa
from apps.convocatorias.models import Convocatoria
from apps.empresas.models import Empresa
from apps.estudiantes.models import EstadoEstudiante, Habilitacion, PerfilEstudiante
from apps.postulaciones.models import EstadoPostulacion, Postulacion, Practica

UBICADOS = [EstadoEstudiante.UBICADO, EstadoEstudiante.EN_PRACTICA, EstadoEstudiante.PRACTICA_FINALIZADA]
ALGUNA_VEZ_HABILITADOS = [EstadoEstudiante.HABILITADO, *UBICADOS]
PRACTICAS_VALIDAS = [Practica.Estado.LEGALIZADA, Practica.Estado.EN_CURSO, Practica.Estado.FINALIZADA]


def _rango(periodo):
    zona = timezone.get_current_timezone()
    return (
        timezone.make_aware(datetime.combine(periodo.fecha_inicio, time.min), zona),
        timezone.make_aware(datetime.combine(periodo.fecha_fin, time.max), zona),
    )


def _porcentaje(parte, total):
    return round(100 * parte / total, 1) if total else 0.0


def calcular(periodo_id=None, programa_id=None):
    periodo = PeriodoAcademico.objects.filter(pk=periodo_id).first() if periodo_id else None
    rango = _rango(periodo) if periodo else None

    estudiantes = PerfilEstudiante.objects.all()
    postulaciones = Postulacion.objects.all()
    practicas = Practica.objects.filter(estado__in=PRACTICAS_VALIDAS)
    convocatorias = Convocatoria.objects.filter(estado=Convocatoria.Estado.PUBLICADA)
    habilitaciones = Habilitacion.objects.filter(accion=Habilitacion.Accion.HABILITADO)
    if programa_id:
        estudiantes = estudiantes.filter(programa_id=programa_id)
        postulaciones = postulaciones.filter(estudiante__programa_id=programa_id)
        practicas = practicas.filter(estudiante__programa_id=programa_id)
        convocatorias = convocatorias.filter(programas=programa_id)
        habilitaciones = habilitaciones.filter(estudiante__programa_id=programa_id)
    if periodo:
        estudiantes = estudiantes.filter(habilitaciones__periodo=periodo).distinct()
        postulaciones = postulaciones.filter(creado_en__range=rango)
        practicas = practicas.filter(legalizada_en__range=rango)
        habilitaciones = habilitaciones.filter(periodo=periodo)

    # ---------------------------------------------------------------- estudiantes
    por_estado = Counter(dict(estudiantes.order_by().values_list("estado").annotate(total=Count("id", distinct=True))))
    habilitados = sum(por_estado[e] for e in ALGUNA_VEZ_HABILITADOS)
    ubicados = sum(por_estado[e] for e in UBICADOS)
    en_busqueda = estudiantes.filter(
        estado=EstadoEstudiante.HABILITADO, postulaciones__estado__in=[
            EstadoPostulacion.POSTULADO, EstadoPostulacion.EN_REVISION, EstadoPostulacion.PRESELECCIONADO,
            EstadoPostulacion.ENTREVISTA, EstadoPostulacion.SELECCIONADO,
        ],
    ).distinct().count()

    # Tiempo desde la (primera) habilitación hasta la legalización
    primera_habilitacion = dict(habilitaciones.order_by().values_list("estudiante").annotate(fecha=Min("creado_en")))
    dias = [
        (p.legalizada_en - primera_habilitacion[p.estudiante_id]).days
        for p in practicas.only("estudiante_id", "legalizada_en") if p.estudiante_id in primera_habilitacion
    ]

    # ---------------------------------------------------------------- convocatorias y postulaciones
    cupos = convocatorias.distinct().aggregate(total=Sum("cupos"))["total"] or 0
    total_postulaciones = postulaciones.count()
    embudo = Counter(dict(postulaciones.order_by().values_list("estado").annotate(total=Count("id"))))

    # ---------------------------------------------------------------- por programa
    filas = defaultdict(lambda: {"registrados": 0, "habilitados": 0, "ubicados": 0, "postulaciones": 0})
    for programa, estado, total in estudiantes.order_by().values_list("programa", "estado").annotate(total=Count("id", distinct=True)):
        filas[programa]["registrados"] += total
        filas[programa]["habilitados"] += total if estado in ALGUNA_VEZ_HABILITADOS else 0
        filas[programa]["ubicados"] += total if estado in UBICADOS else 0
    for programa, total in postulaciones.order_by().values_list("estudiante__programa").annotate(total=Count("id")):
        filas[programa]["postulaciones"] += total
    nombres = dict(Programa.objects.filter(pk__in=filas).values_list("id", "nombre"))
    por_programa = sorted(
        ({"programa": nombres.get(pid, "—"), **datos, "porcentaje_ubicacion": _porcentaje(datos["ubicados"], datos["habilitados"])}
         for pid, datos in filas.items()),
        key=lambda f: (-f["habilitados"], f["programa"]),
    )

    # ---------------------------------------------------------------- tendencia de los últimos meses
    def por_mes(consulta, campo):
        return {mes.strftime("%Y-%m"): total for mes, total in consulta.annotate(mes=TruncMonth(campo)).order_by().values_list("mes").annotate(total=Count("id"))}

    postulaciones_mes = por_mes(postulaciones, "creado_en")
    legalizaciones_mes = por_mes(practicas, "legalizada_en")
    meses = sorted(set(postulaciones_mes) | set(legalizaciones_mes))[-6:]

    return {
        "filtros": {
            "periodo": periodo.codigo if periodo else None,
            "programa": Programa.objects.filter(pk=programa_id).values_list("nombre", flat=True).first() if programa_id else None,
        },
        "estudiantes": {
            "registrados": sum(por_estado.values()),
            "habilitados": habilitados,
            "en_busqueda": en_busqueda,
            "ubicados": ubicados,
            "porcentaje_ubicacion": _porcentaje(ubicados, habilitados),
            "dias_promedio_hasta_ubicacion": round(sum(dias) / len(dias), 1) if dias else None,
        },
        "oferta": {
            "convocatorias_activas": convocatorias.distinct().count(),
            "cupos_ofertados": cupos,
            "postulaciones": total_postulaciones,
            "postulaciones_por_cupo": round(total_postulaciones / cupos, 2) if cupos else None,
            "empresas_aliadas": Empresa.objects.filter(estado=Empresa.Estado.ALIADA).count(),
            "empresas_pendientes": Empresa.objects.filter(estado=Empresa.Estado.PENDIENTE).count(),
        },
        "embudo": [{"estado": e.value, "nombre": e.label, "total": embudo.get(e.value, 0)} for e in EstadoPostulacion],
        "por_programa": por_programa,
        "tendencia": [{"mes": m, "postulaciones": postulaciones_mes.get(m, 0), "legalizaciones": legalizaciones_mes.get(m, 0)} for m in meses],
    }
