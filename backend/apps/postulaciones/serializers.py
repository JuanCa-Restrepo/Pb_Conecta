from rest_framework import serializers

from apps.comun.archivos import validar_pdf
from apps.comun.opciones import TipoVinculacion

from apps.convocatorias import afinidad
from apps.convocatorias.models import Convocatoria
from apps.cuentas.models import Rol
from apps.estudiantes.serializers import PerfilProfesionalSerializer

from . import servicios
from .models import EntradaSeguimiento, Entrevista, EstadoPostulacion, HistorialEstado, Postulacion, Practica, VerificacionRequisitos


class HistorialSerializer(serializers.ModelSerializer):
    estado_nuevo_nombre = serializers.CharField(source="get_estado_nuevo_display")
    usuario = serializers.SerializerMethodField()

    class Meta:
        model = HistorialEstado
        fields = ["id", "estado_anterior", "estado_nuevo", "estado_nuevo_nombre", "usuario", "comentario", "creado_en"]

    def get_usuario(self, fila):
        return fila.usuario.nombre_completo if fila.usuario else "Sistema"


class EntrevistaSerializer(serializers.ModelSerializer):
    modalidad_nombre = serializers.CharField(source="get_modalidad_display", read_only=True)
    estado_nombre = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = Entrevista
        fields = ["id", "fecha_hora", "modalidad", "modalidad_nombre", "lugar_o_enlace", "notas", "estado", "estado_nombre", "creado_en"]
        read_only_fields = ["estado"]


class SeguimientoSerializer(serializers.ModelSerializer):
    autor = serializers.CharField(source="autor.nombre_completo", read_only=True)
    autor_rol = serializers.CharField(source="autor.get_rol_display", read_only=True)
    tipo_nombre = serializers.CharField(source="get_tipo_display", read_only=True)
    canal_nombre = serializers.CharField(source="get_canal_display", read_only=True, default=None)

    class Meta:
        model = EntradaSeguimiento
        fields = ["id", "tipo", "tipo_nombre", "canal", "canal_nombre", "fecha_contacto", "texto", "autor", "autor_rol", "creado_en"]


class CambioEstadoSerializer(serializers.Serializer):
    estado = serializers.ChoiceField(choices=EstadoPostulacion.choices)
    comentario = serializers.CharField(required=False, allow_blank=True, default="")
    motivo = serializers.CharField(required=False, allow_blank=True, default="")


class CrearPostulacionSerializer(serializers.Serializer):
    convocatoria = serializers.PrimaryKeyRelatedField(queryset=Convocatoria.objects.all())
    mensaje_presentacion = serializers.CharField(required=False, allow_blank=True, default="", max_length=2000)


class PostulacionListaSerializer(serializers.ModelSerializer):
    estado_nombre = serializers.CharField(source="get_estado_display", read_only=True)
    convocatoria = serializers.SerializerMethodField()
    estudiante = serializers.SerializerMethodField()
    proxima_entrevista = serializers.SerializerMethodField()

    class Meta:
        model = Postulacion
        fields = [
            "id", "estado", "estado_nombre", "afinidad", "motivo_no_seleccion", "convocatoria", "estudiante",
            "proxima_entrevista", "creado_en", "actualizado_en",
        ]

    def get_convocatoria(self, p):
        c = p.convocatoria
        return {"id": c.id, "titulo": c.titulo, "empresa": c.empresa.razon_social, "estado": c.estado, "estado_nombre": c.get_estado_display()}

    def get_estudiante(self, p):
        e = p.estudiante
        return {"id": e.id, "nombre": e.usuario.nombre_completo, "programa": e.programa.nombre, "semestre": e.semestre}

    def get_proxima_entrevista(self, p):
        programadas = [e for e in p.entrevistas.all() if e.estado == Entrevista.Estado.PROGRAMADA]
        return EntrevistaSerializer(programadas[-1]).data if programadas else None


class VerificacionSerializer(serializers.ModelSerializer):
    funcionario = serializers.CharField(source="funcionario.nombre_completo", read_only=True)
    resultado_nombre = serializers.CharField(source="get_resultado_display", read_only=True)

    class Meta:
        model = VerificacionRequisitos
        fields = ["id", "resultado", "resultado_nombre", "observacion", "funcionario", "creado_en"]


class PracticaSerializer(serializers.ModelSerializer):
    estado_nombre = serializers.CharField(source="get_estado_display", read_only=True)
    tipo_vinculacion_nombre = serializers.CharField(source="get_tipo_vinculacion_display", read_only=True)
    estudiante = serializers.SerializerMethodField()
    convocatoria = serializers.SerializerMethodField()
    legalizada_por = serializers.CharField(source="legalizada_por.nombre_completo", read_only=True)
    tiene_documento = serializers.SerializerMethodField()

    class Meta:
        model = Practica
        fields = [
            "id", "postulacion", "estado", "estado_nombre", "fecha_inicio", "fecha_fin", "tipo_vinculacion",
            "tipo_vinculacion_nombre", "asesor_nombre", "tutor_empresa_nombre", "tutor_empresa_email", "observacion_cierre",
            "estudiante", "convocatoria", "legalizada_por", "legalizada_en", "finalizada_en", "tiene_documento",
        ]

    def get_estudiante(self, practica):
        e = practica.estudiante
        return {"id": e.id, "nombre": e.usuario.nombre_completo, "programa": e.programa.nombre, "email": e.usuario.email}

    def get_convocatoria(self, practica):
        c = practica.postulacion.convocatoria
        return {"id": c.id, "titulo": c.titulo, "empresa": c.empresa.razon_social}

    def get_tiene_documento(self, practica):
        return bool(practica.documento_soporte)


class VerificarSerializer(serializers.Serializer):
    resultado = serializers.ChoiceField(choices=VerificacionRequisitos.Resultado.choices)
    observacion = serializers.CharField(required=False, allow_blank=True, default="")


class LegalizarSerializer(serializers.Serializer):
    fecha_inicio = serializers.DateField()
    fecha_fin = serializers.DateField()
    tipo_vinculacion = serializers.ChoiceField(choices=TipoVinculacion.choices)
    asesor_nombre = serializers.CharField(max_length=150)
    tutor_empresa_nombre = serializers.CharField(max_length=150)
    tutor_empresa_email = serializers.EmailField(required=False, allow_blank=True, default="")
    documento_soporte = serializers.FileField(required=False, validators=[validar_pdf])


class PostulacionDetalleSerializer(PostulacionListaSerializer):
    historial = HistorialSerializer(many=True, read_only=True)
    entrevistas = EntrevistaSerializer(many=True, read_only=True)
    seguimiento = serializers.SerializerMethodField()
    contacto_empresa = serializers.SerializerMethodField()
    perfil_estudiante = serializers.SerializerMethodField()
    afinidad_detalle = serializers.SerializerMethodField()
    acciones = serializers.SerializerMethodField()
    verificaciones = serializers.SerializerMethodField()
    practica = serializers.SerializerMethodField()

    class Meta(PostulacionListaSerializer.Meta):
        fields = PostulacionListaSerializer.Meta.fields + [
            "mensaje_presentacion", "historial", "entrevistas", "seguimiento", "contacto_empresa", "perfil_estudiante",
            "afinidad_detalle", "acciones", "verificaciones", "practica",
        ]

    def get_verificaciones(self, p):
        """RF-62a: la verificación es un trámite de la oficina; el estudiante y la empresa ven solo la práctica resultante."""
        if self._usuario.rol not in (Rol.OFICINA, Rol.SUPERADMIN):
            return []
        return VerificacionSerializer(p.verificaciones.select_related("funcionario"), many=True).data

    def get_practica(self, p):
        practica = getattr(p, "practica", None)
        return PracticaSerializer(practica).data if practica else None

    @property
    def _usuario(self):
        return self.context["request"].user

    def get_seguimiento(self, p):
        entradas = p.seguimiento.all()
        if self._usuario.rol not in (Rol.OFICINA, Rol.SUPERADMIN):  # RF-59: las notas internas son solo de la oficina
            entradas = [e for e in entradas if e.tipo != EntradaSeguimiento.Tipo.NOTA_INTERNA]
        return SeguimientoSerializer(entradas, many=True).data

    def get_contacto_empresa(self, p):
        """RF-58: el estudiante ve el contacto de la empresa desde la preselección; la empresa y la oficina siempre."""
        if self._usuario.rol == Rol.ESTUDIANTE and p.estado not in servicios.ESTADOS_CON_CONTACTO:
            return None
        empresa = p.convocatoria.empresa
        return {"nombre": empresa.contacto_nombre, "email": empresa.contacto_email, "telefono": empresa.contacto_telefono}

    def get_perfil_estudiante(self, p):
        if self._usuario.rol == Rol.ESTUDIANTE:
            return None
        return PerfilProfesionalSerializer(p.estudiante).data

    def get_afinidad_detalle(self, p):
        return afinidad.calcular(p.estudiante, p.convocatoria)

    def get_acciones(self, p):
        return servicios.acciones_permitidas(p, self._usuario)


class EntradaNuevaSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=EntradaSeguimiento.Tipo.choices, default=EntradaSeguimiento.Tipo.MENSAJE)
    texto = serializers.CharField(max_length=3000)
    canal = serializers.ChoiceField(choices=EntradaSeguimiento.Canal.choices, required=False, allow_null=True)
    fecha_contacto = serializers.DateTimeField(required=False, allow_null=True)
