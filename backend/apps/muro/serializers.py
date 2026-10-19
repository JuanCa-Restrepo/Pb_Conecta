from rest_framework import serializers

from apps.catalogos.models import Programa
from apps.comun.archivos import validar_imagen

from . import servicios
from .models import Comentario, Publicacion


class PublicacionSerializer(serializers.ModelSerializer):
    tipo_nombre = serializers.CharField(source="get_tipo_display", read_only=True)
    estado_nombre = serializers.CharField(source="get_estado_display", read_only=True)
    imagen = serializers.SerializerMethodField()
    autor = serializers.SerializerMethodField()
    empresa = serializers.SerializerMethodField()
    convocatoria = serializers.SerializerMethodField()
    programas_detalle = serializers.SerializerMethodField()
    reacciones_total = serializers.IntegerField(read_only=True, default=0)
    comentarios_total = serializers.IntegerField(read_only=True, default=0)
    me_interesa = serializers.BooleanField(read_only=True, default=False)
    guardada = serializers.BooleanField(read_only=True, default=False)
    puede_editar = serializers.SerializerMethodField()
    puede_moderar = serializers.SerializerMethodField()
    motivo_ocultamiento = serializers.SerializerMethodField()

    class Meta:
        model = Publicacion
        fields = [
            "id", "tipo", "tipo_nombre", "titulo", "texto", "imagen", "enlace_url", "fuente_externa", "fecha_evento",
            "lugar_evento", "para_todos_programas", "programas_detalle", "autor", "empresa", "convocatoria", "estado",
            "estado_nombre", "motivo_ocultamiento", "reacciones_total", "comentarios_total", "me_interesa", "guardada",
            "puede_editar", "puede_moderar", "creado_en",
        ]

    @property
    def _usuario(self):
        return self.context["request"].user

    def get_imagen(self, p):
        return p.imagen.url if p.imagen else None

    def get_autor(self, p):
        return {"nombre": p.autor.nombre_completo, "rol": p.autor.get_rol_display()}

    def get_empresa(self, p):
        if not p.empresa:
            return None
        return {"id": p.empresa.id, "razon_social": p.empresa.razon_social, "logo": p.empresa.logo.url if p.empresa.logo else None}

    def get_convocatoria(self, p):
        c = p.convocatoria
        if not c:
            return None
        return {"id": c.id, "estado": c.estado, "estado_nombre": c.get_estado_display(), "fecha_cierre": c.fecha_cierre,
                "modalidad_nombre": c.get_modalidad_display()}

    def get_programas_detalle(self, p):
        return [{"id": pr.id, "nombre": pr.nombre} for pr in p.programas.all()]

    def get_puede_editar(self, p):
        return servicios.puede_editar(p, self._usuario)

    def get_puede_moderar(self, p):
        return servicios.es_oficina(self._usuario)

    def get_motivo_ocultamiento(self, p):
        return p.motivo_ocultamiento if servicios.es_oficina(self._usuario) else ""


class BooleanoOpcional(serializers.BooleanField):
    """En multipart, DRF lee un booleano ausente como False (casilla HTML sin marcar). Aquí ausente = no enviado."""

    default_empty_html = serializers.empty


class PublicacionEntradaSerializer(serializers.ModelSerializer):
    """Crear o editar (multipart para la imagen). El tipo no se puede cambiar al editar."""

    imagen = serializers.ImageField(required=False, allow_null=True, validators=[validar_imagen])
    para_todos_programas = BooleanoOpcional(required=False)
    programas = serializers.PrimaryKeyRelatedField(queryset=Programa.objects.filter(activo=True), many=True, required=False)

    class Meta:
        model = Publicacion
        fields = ["tipo", "titulo", "texto", "imagen", "enlace_url", "fuente_externa", "fecha_evento", "lugar_evento",
                  "para_todos_programas", "programas"]
        extra_kwargs = {"tipo": {"required": False}}

    def validate_tipo(self, valor):
        if valor == Publicacion.Tipo.CONVOCATORIA:
            raise serializers.ValidationError("Las convocatorias llegan al muro solas cuando la oficina las aprueba.")
        return valor


class ComentarioSerializer(serializers.ModelSerializer):
    autor = serializers.CharField(source="autor.nombre_completo", read_only=True)
    autor_rol = serializers.CharField(source="autor.get_rol_display", read_only=True)

    class Meta:
        model = Comentario
        fields = ["id", "texto", "autor", "autor_rol", "oculto", "creado_en"]
        read_only_fields = ["oculto"]
