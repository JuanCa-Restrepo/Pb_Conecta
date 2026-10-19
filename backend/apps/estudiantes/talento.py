"""Búsqueda de talento por parte de las empresas aliadas e invitación a postularse (RF-45)."""

from django.db.models import Count, Q

from apps.comun.errores import ErrorRegla
from apps.convocatorias.models import Convocatoria
from apps.notificaciones.models import Notificacion
from apps.notificaciones.servicios import notificar
from apps.postulaciones.models import Postulacion

from .models import EstadoEstudiante, PerfilEstudiante

TIPO_INVITACION = "INVITACION"


def candidatos():
    """RN-10: la empresa solo ve a estudiantes habilitados que activaron «Abierto a oportunidades» (RF-17)."""
    return PerfilEstudiante.objects.filter(
        abierto_oportunidades=True, estado=EstadoEstudiante.HABILITADO, usuario__is_active=True
    ).select_related("usuario", "programa", "ciudad").prefetch_related(
        "estudiantehabilidad_set__habilidad", "idiomas", "experiencias", "proyectos", "certificaciones", "enlaces"
    )


def buscar(parametros):
    consulta = candidatos()
    if programa := parametros.get("programa"):
        consulta = consulta.filter(programa_id=programa)
    if modalidad := parametros.get("modalidad"):
        consulta = consulta.filter(Q(modalidad_preferida=modalidad) | Q(modalidad_preferida="HIBRIDA"))
    if ciudad := parametros.get("ciudad"):
        consulta = consulta.filter(ciudad_id=ciudad)
    if texto := parametros.get("q", "").strip():
        consulta = consulta.filter(
            Q(titular__icontains=texto) | Q(acerca_de__icontains=texto)
            | Q(usuario__nombres__icontains=texto) | Q(usuario__apellidos__icontains=texto)
        )
    if habilidades := [h for h in parametros.get("habilidades", "").split(",") if h.isdigit()]:
        # Primero quienes tienen más de las habilidades buscadas
        consulta = consulta.annotate(
            coincidencias=Count("habilidades", filter=Q(habilidades__in=habilidades), distinct=True)
        ).filter(coincidencias__gt=0).order_by("-coincidencias", "usuario__apellidos")
    else:
        consulta = consulta.order_by("-actualizado_en")
    return consulta


def invitar(empresa, usuario, perfil, convocatoria, mensaje=""):
    """Avisa al estudiante de una convocatoria de la empresa. No crea la postulación: el estudiante decide."""
    if convocatoria.empresa_id != empresa.pk or convocatoria.estado != Convocatoria.Estado.PUBLICADA:
        raise ErrorRegla("Solo puedes invitar a una convocatoria publicada de tu empresa.")
    if not convocatoria.programas.filter(pk=perfil.programa_id).exists():
        raise ErrorRegla("La convocatoria no incluye el programa del estudiante, así que no podría postularse (RN-05).")
    if Postulacion.objects.filter(estudiante=perfil, convocatoria=convocatoria).exists():
        raise ErrorRegla("El estudiante ya se postuló a esta convocatoria.")
    url = f"/estudiante/convocatorias/{convocatoria.pk}"
    if Notificacion.objects.filter(usuario=perfil.usuario, tipo=TIPO_INVITACION, url_destino=url).exists():
        raise ErrorRegla("Ya invitaste a este estudiante a esta convocatoria.")

    detalle = f" Mensaje de {usuario.nombres}: «{mensaje.strip()}»" if mensaje.strip() else ""
    return notificar(
        perfil.usuario, TIPO_INVITACION, f"{empresa.razon_social} te invita a postularte",
        f"Revisaron tu perfil y creen que encajas en «{convocatoria.titulo}».{detalle}", url=url,
    )
