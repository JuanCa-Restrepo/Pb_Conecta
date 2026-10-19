"""Exportación de listados a CSV (RF-81). Separador «;» y BOM UTF-8 para que Excel en español lo abra con tildes."""

import csv
import io

from django.utils import timezone

from apps.convocatorias.models import Convocatoria
from apps.empresas.models import Empresa
from apps.estudiantes.models import PerfilEstudiante
from apps.postulaciones.models import Postulacion, Practica


def _fecha(valor):
    if not valor:
        return ""
    return timezone.localtime(valor).strftime("%d/%m/%Y %H:%M") if hasattr(valor, "hour") else valor.strftime("%d/%m/%Y")


def _estudiantes():
    yield ["Nombre", "Correo", "Programa", "Semestre", "Estado", "Teléfono", "Abierto a oportunidades"]
    for e in PerfilEstudiante.objects.select_related("usuario", "programa").order_by("usuario__apellidos"):
        yield [e.usuario.nombre_completo, e.usuario.email, e.programa.nombre, e.semestre or "", e.get_estado_display(),
               e.usuario.telefono, "Sí" if e.abierto_oportunidades else "No"]


def _postulaciones():
    yield ["Estudiante", "Programa", "Convocatoria", "Empresa", "Estado", "Afinidad", "Postulado", "Última actualización"]
    for p in Postulacion.objects.select_related("estudiante__usuario", "estudiante__programa", "convocatoria__empresa").order_by("-creado_en"):
        yield [p.estudiante.usuario.nombre_completo, p.estudiante.programa.nombre, p.convocatoria.titulo,
               p.convocatoria.empresa.razon_social, p.get_estado_display(), p.afinidad, _fecha(p.creado_en), _fecha(p.actualizado_en)]


def _practicas():
    yield ["Estudiante", "Programa", "Empresa", "Convocatoria", "Estado", "Inicio", "Fin", "Vinculación", "Docente asesor",
           "Tutor en la empresa", "Legalizada"]
    for p in Practica.objects.select_related("estudiante__usuario", "estudiante__programa", "postulacion__convocatoria__empresa").order_by("-legalizada_en"):
        c = p.postulacion.convocatoria
        yield [p.estudiante.usuario.nombre_completo, p.estudiante.programa.nombre, c.empresa.razon_social, c.titulo,
               p.get_estado_display(), _fecha(p.fecha_inicio), _fecha(p.fecha_fin), p.get_tipo_vinculacion_display(),
               p.asesor_nombre, p.tutor_empresa_nombre, _fecha(p.legalizada_en)]


def _convocatorias():
    yield ["Título", "Empresa", "Estado", "Modalidad", "Cupos", "Postulaciones", "Programas afines", "Cierre", "Publicada"]
    for c in Convocatoria.objects.select_related("empresa").prefetch_related("programas", "postulaciones").order_by("-creado_en"):
        yield [c.titulo, c.empresa.razon_social, c.get_estado_display(), c.get_modalidad_display(), c.cupos,
               len(c.postulaciones.all()), ", ".join(p.nombre for p in c.programas.all()), _fecha(c.fecha_cierre), _fecha(c.publicada_en)]


def _empresas():
    yield ["Razón social", "NIT", "Sector", "Ciudad", "Estado", "Convenio vigente hasta", "Contacto", "Correo", "Teléfono"]
    for e in Empresa.objects.select_related("sector", "ciudad").prefetch_related("convenios").order_by("razon_social"):
        vigente = e.convenio_vigente()
        yield [e.razon_social, e.nit, e.sector.nombre, e.ciudad.nombre, e.get_estado_display(),
               _fecha(vigente.fecha_fin) if vigente else "", e.contacto_nombre, e.contacto_email, e.contacto_telefono]


REPORTES = {
    "estudiantes": _estudiantes,
    "postulaciones": _postulaciones,
    "practicas": _practicas,
    "convocatorias": _convocatorias,
    "empresas": _empresas,
}


def generar(reporte):
    contenido = io.StringIO()
    contenido.write("﻿")  # BOM: Excel reconoce UTF-8
    escritor = csv.writer(contenido, delimiter=";")
    for fila in REPORTES[reporte]():
        escritor.writerow(fila)
    return contenido.getvalue()
