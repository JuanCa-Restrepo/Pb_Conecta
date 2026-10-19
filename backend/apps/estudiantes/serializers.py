"""Perfil del estudiante (M2): el que edita el propio estudiante y la vista profesional que ven las empresas (RF-16)."""

from rest_framework import serializers

from apps.catalogos.models import Habilidad

from . import servicios
from .models import Certificacion, Enlace, EstudianteHabilidad, Experiencia, IdiomaEstudiante, PerfilEstudiante, Proyecto


class HabilidadPerfilSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source="habilidad.id")
    nombre = serializers.CharField(source="habilidad.nombre")
    nivel_nombre = serializers.CharField(source="get_nivel_display")

    class Meta:
        model = EstudianteHabilidad
        fields = ["id", "nombre", "nivel", "nivel_nombre"]


class IdiomaSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdiomaEstudiante
        fields = ["id", "idioma", "nivel"]


class ExperienciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experiencia
        fields = ["id", "cargo", "organizacion", "fecha_inicio", "fecha_fin", "descripcion"]

    def validate(self, datos):
        inicio = datos.get("fecha_inicio", getattr(self.instance, "fecha_inicio", None))
        fin = datos.get("fecha_fin", getattr(self.instance, "fecha_fin", None))
        if inicio and fin and fin < inicio:
            raise serializers.ValidationError({"fecha_fin": "La fecha de fin no puede ser anterior a la de inicio."})
        return datos


class ProyectoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proyecto
        fields = ["id", "titulo", "descripcion", "url"]


class CertificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certificacion
        fields = ["id", "nombre", "entidad", "fecha", "url"]


class EnlaceSerializer(serializers.ModelSerializer):
    tipo_nombre = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = Enlace
        fields = ["id", "tipo", "tipo_nombre", "url"]


class PerfilBase(serializers.ModelSerializer):
    """Campos que comparten el perfil propio y la vista profesional."""

    nombre = serializers.CharField(source="usuario.nombre_completo", read_only=True)
    programa_nombre = serializers.CharField(source="programa.nombre", read_only=True)
    nivel_programa = serializers.CharField(source="programa.get_nivel_display", read_only=True)
    ciudad_nombre = serializers.CharField(source="ciudad.nombre", read_only=True, default=None)
    jornada_nombre = serializers.CharField(source="get_jornada_display", read_only=True, default=None)
    modalidad_preferida_nombre = serializers.CharField(source="get_modalidad_preferida_display", read_only=True, default=None)
    estado_nombre = serializers.CharField(source="get_estado_display", read_only=True)
    habilidades = HabilidadPerfilSerializer(source="estudiantehabilidad_set", many=True, read_only=True)
    idiomas = IdiomaSerializer(many=True, read_only=True)
    experiencias = ExperienciaSerializer(many=True, read_only=True)
    proyectos = ProyectoSerializer(many=True, read_only=True)
    certificaciones = CertificacionSerializer(many=True, read_only=True)
    enlaces = EnlaceSerializer(many=True, read_only=True)
    tiene_hoja_vida = serializers.SerializerMethodField()

    CAMPOS = [
        "id", "nombre", "programa", "programa_nombre", "nivel_programa", "semestre", "ciudad", "ciudad_nombre", "titular",
        "acerca_de", "fecha_disponible", "jornada", "jornada_nombre", "modalidad_preferida", "modalidad_preferida_nombre",
        "estado", "estado_nombre", "habilidades", "idiomas", "experiencias", "proyectos", "certificaciones", "enlaces",
        "tiene_hoja_vida",
    ]

    def get_tiene_hoja_vida(self, perfil):
        return bool(perfil.hoja_vida)


class PerfilPropioSerializer(PerfilBase):
    """GET/PATCH /estudiantes/yo/. El programa y el estado los gestiona la oficina, por eso son de solo lectura."""

    email = serializers.CharField(source="usuario.email", read_only=True)
    nombres = serializers.CharField(source="usuario.nombres", max_length=100)
    apellidos = serializers.CharField(source="usuario.apellidos", max_length=100)
    telefono = serializers.CharField(source="usuario.telefono", max_length=20, allow_blank=True)
    completitud = serializers.SerializerMethodField()
    faltantes_para_postular = serializers.SerializerMethodField()

    class Meta:
        model = PerfilEstudiante
        fields = PerfilBase.CAMPOS + [
            "email", "nombres", "apellidos", "telefono", "documento", "abierto_oportunidades", "completitud",
            "faltantes_para_postular",
        ]
        read_only_fields = ["programa", "estado"]

    def get_completitud(self, perfil):
        return servicios.completitud(perfil)

    def get_faltantes_para_postular(self, perfil):
        return servicios.faltantes_perfil_minimo(perfil)

    def validate_semestre(self, valor):
        if valor is not None and not 1 <= valor <= 12:
            raise serializers.ValidationError("El semestre debe estar entre 1 y 12.")
        return valor

    def validate_documento(self, valor):
        valor = (valor or "").strip() or None
        if valor and PerfilEstudiante.objects.exclude(pk=self.instance.pk).filter(documento=valor).exists():
            raise serializers.ValidationError("Este documento ya está registrado en otra cuenta.")
        return valor

    def update(self, perfil, datos):
        datos_usuario = datos.pop("usuario", {})
        for campo, valor in datos_usuario.items():
            setattr(perfil.usuario, campo, valor.strip() if isinstance(valor, str) else valor)
        if datos_usuario:
            perfil.usuario.save(update_fields=list(datos_usuario))
        return super().update(perfil, datos)


class PerfilProfesionalSerializer(PerfilBase):
    """RF-16: lo que ven las empresas y la oficina. Nunca incluye el número de documento."""

    email = serializers.CharField(source="usuario.email", read_only=True)
    telefono = serializers.CharField(source="usuario.telefono", read_only=True)

    class Meta:
        model = PerfilEstudiante
        fields = PerfilBase.CAMPOS + ["email", "telefono"]
        read_only_fields = fields


class HabilidadElegidaSerializer(serializers.Serializer):
    habilidad = serializers.PrimaryKeyRelatedField(queryset=Habilidad.objects.all(), required=False)
    nombre = serializers.CharField(max_length=80, required=False)
    nivel = serializers.ChoiceField(choices=EstudianteHabilidad.Nivel.choices, default=EstudianteHabilidad.Nivel.BASICO)

    def validate(self, datos):
        if not datos.get("habilidad") and not (datos.get("nombre") or "").strip():
            raise serializers.ValidationError("Elige una habilidad del catálogo o escribe su nombre.")
        return datos


class HabilidadesSerializer(serializers.Serializer):
    habilidades = HabilidadElegidaSerializer(many=True, max_length=30)
