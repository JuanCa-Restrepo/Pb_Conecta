"""Alertas de seguimiento para la oficina de prácticas (RF-66 · problema P3: falta de asesoramiento continuo).

Se calculan en el momento a partir de los datos, así siempre están al día. Los días de cada alerta son parámetros
editables en el admin (tabla `parametro`).
"""

from datetime import timedelta

from django.db.models import Count, Max, Min, Q
from django.utils import timezone

from apps.catalogos.models import Parametro
from apps.convocatorias.models import Convocatoria
from apps.empresas.models import Empresa
from apps.estudiantes.models import EstadoEstudiante, Habilitacion, PerfilEstudiante
from apps.postulaciones.models import EstadoPostulacion, Postulacion

MAX_ITEMS = 50


def _categoria(clave, titulo, descripcion, gravedad, items):
    return {"clave": clave, "titulo": titulo, "descripcion": descripcion, "gravedad": gravedad,
            "total": len(items), "items": items[:MAX_ITEMS]}


def calcular(hoy=None):
    hoy = hoy or timezone.localdate()
    ahora = timezone.now()
    dias = {
        "sin_postular": Parametro.entero("dias_sin_postular", 15),
        "sin_respuesta": Parametro.entero("dias_sin_respuesta", 10),
        "sin_ubicar": Parametro.entero("dias_sin_ubicar", 60),
        "convocatoria": Parametro.entero("dias_convocatoria_sin_postulantes", 7),
        "convenio": Parametro.entero("dias_aviso_convenio", 30),
    }
    hace = lambda n: ahora - timedelta(days=n)  # noqa: E731

    # 1. Seleccionados que esperan verificación y legalización: es el trámite que depende de la oficina
    por_legalizar = [
        {"id": p.id, "titulo": p.estudiante.usuario.nombre_completo,
         "detalle": f"{p.convocatoria.titulo} · {p.convocatoria.empresa}", "desde": p.actualizado_en,
         "url": f"/oficina/postulaciones/{p.id}"}
        for p in Postulacion.objects.filter(estado=EstadoPostulacion.SELECCIONADO)
        .select_related("estudiante__usuario", "convocatoria__empresa").order_by("actualizado_en")
    ]

    # 2. Habilitados que no se han postulado a nada
    ultima_habilitacion = Max("habilitaciones__creado_en", filter=Q(habilitaciones__accion=Habilitacion.Accion.HABILITADO))
    sin_postular = [
        {"id": e.id, "titulo": e.usuario.nombre_completo, "detalle": e.programa.nombre, "desde": e.habilitado_en,
         "url": "/oficina/estudiantes"}
        for e in PerfilEstudiante.objects.filter(estado=EstadoEstudiante.HABILITADO)
        .annotate(habilitado_en=ultima_habilitacion, postulaciones_total=Count("postulaciones"))
        .filter(postulaciones_total=0, habilitado_en__lt=hace(dias["sin_postular"]))
        .select_related("usuario", "programa").order_by("habilitado_en")
    ]

    # 3. Postulaciones que la empresa no ha revisado
    sin_respuesta = [
        {"id": p.id, "titulo": p.estudiante.usuario.nombre_completo,
         "detalle": f"{p.convocatoria.titulo} · {p.convocatoria.empresa}", "desde": p.creado_en,
         "url": f"/oficina/postulaciones/{p.id}"}
        for p in Postulacion.objects.filter(estado=EstadoPostulacion.POSTULADO, creado_en__lt=hace(dias["sin_respuesta"]))
        .select_related("estudiante__usuario", "convocatoria__empresa").order_by("creado_en")
    ]

    # 4. Habilitados que llevan tiempo postulándose sin ubicarse
    sin_ubicar = [
        {"id": e.id, "titulo": e.usuario.nombre_completo, "detalle": f"{e.programa.nombre} · {e.postulaciones_total} postulación(es)",
         "desde": e.primera_postulacion, "url": "/oficina/estudiantes"}
        for e in PerfilEstudiante.objects.filter(estado=EstadoEstudiante.HABILITADO)
        .annotate(primera_postulacion=Min("postulaciones__creado_en"), postulaciones_total=Count("postulaciones"))
        .filter(primera_postulacion__lt=hace(dias["sin_ubicar"]))
        .select_related("usuario", "programa").order_by("primera_postulacion")
    ]

    # 5. Convocatorias publicadas que nadie ha aprovechado
    convocatorias_vacias = [
        {"id": c.id, "titulo": c.titulo, "detalle": f"{c.empresa} · cierra el {c.fecha_cierre:%d/%m/%Y}", "desde": c.publicada_en,
         "url": f"/oficina/convocatorias/{c.id}"}
        for c in Convocatoria.objects.filter(estado=Convocatoria.Estado.PUBLICADA, publicada_en__lt=hace(dias["convocatoria"]))
        .annotate(postulaciones_total=Count("postulaciones")).filter(postulaciones_total=0)
        .select_related("empresa").order_by("publicada_en")
    ]

    # 6. Empresas aliadas cuyo convenio vigente termina pronto
    convenios = []
    for empresa in Empresa.objects.filter(estado=Empresa.Estado.ALIADA).prefetch_related("convenios"):
        vigente = empresa.convenio_vigente(hoy)
        if vigente and vigente.fecha_fin <= hoy + timedelta(days=dias["convenio"]):
            convenios.append({"id": empresa.id, "titulo": empresa.razon_social,
                              "detalle": f"Convenio {vigente.numero} vence el {vigente.fecha_fin:%d/%m/%Y}",
                              "desde": None, "url": f"/oficina/empresas/{empresa.id}"})

    categorias = [
        _categoria("por_legalizar", "Seleccionados por legalizar", "Verifica requisitos en persona y legaliza la práctica.", "alta", por_legalizar),
        _categoria("sin_respuesta", "Postulaciones sin respuesta",
                   f"La empresa no las ha revisado en más de {dias['sin_respuesta']} días.", "media", sin_respuesta),
        _categoria("sin_postular", "Habilitados sin postularse",
                   f"Más de {dias['sin_postular']} días habilitados y ninguna postulación: pueden necesitar asesoría.", "media", sin_postular),
        _categoria("sin_ubicar", "Estudiantes sin ubicar",
                   f"Llevan más de {dias['sin_ubicar']} días postulándose sin conseguir práctica.", "media", sin_ubicar),
        _categoria("convocatorias_sin_postulantes", "Convocatorias sin postulantes",
                   f"Publicadas hace más de {dias['convocatoria']} días sin ninguna postulación.", "baja", convocatorias_vacias),
        _categoria("convenios_por_vencer", "Convenios por vencer", f"Vencen en los próximos {dias['convenio']} días.", "baja", convenios),
    ]
    return {"total": sum(c["total"] for c in categorias), "categorias": categorias}
