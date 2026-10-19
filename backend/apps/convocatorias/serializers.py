from django.utils import timezone
from rest_framework import serializers

from apps.catalogos.models import Habilidad, Programa
from apps.comun.opciones import Modalidad
from apps.cuentas.models import Rol
from apps.empresas.models import Empresa

from apps.postulaciones import servicios as servicios_postulacion

from . import afinidad, servicios
from .models import Convocatoria


class ConvocatoriaSerializer(serializers.ModelSerializer):
    empresa = serializers.PrimaryKeyRelatedField(queryset=Empresa.objects.all(), required=False)
    empresa_nombre = serializers.CharField(source="empresa.razon_social", read_only=True)
    ciudad_nombre = serializers.CharField(source="ciudad.nombre", read_only=True, default=None)
    estado_nombre = serializers.CharField(source="get_estado_display", read_only=True)
    modalidad_nombre = serializers.CharField(source="get_modalidad_display", read_only=True)
    tipo_vinculacion_nombre = serializers.CharField(source="get_tipo_vinculacion_display", read_only=True)
    nivel_formacion_nombre = serializers.CharField(source="get_nivel_formacion_display", read_only=True)
    motivo_cierre_nombre = serializers.CharField(source="get_motivo_cierre_display", read_only=True, default=None)
    programas = serializers.PrimaryKeyRelatedField(queryset=Programa.objects.filter(activo=True), many=True, allow_empty=False)
    programas_detalle = serializers.SerializerMethodField()
    habilidades = serializers.PrimaryKeyRelatedField(queryset=Habilidad.objects.all(), many=True, required=False)
    habilidades_detalle = serializers.SerializerMethodField()
    creada_por_nombre = serializers.CharField(source="creada_por.nombre_completo", read_only=True)
    creada_por_oficina = serializers.SerializerMethodField()
    acciones = serializers.SerializerMethodField()
    postulantes = serializers.SerializerMethodField()
    para_estudiante = serializers.SerializerMethodField()

    class Meta:
        model = Convocatoria
        fields = [
            "id", "empresa", "empresa_nombre", "titulo", "descripcion", "funciones", "nivel_formacion",
            "nivel_formacion_nombre", "modalidad", "modalidad_nombre", "ciudad", "ciudad_nombre", "tipo_vinculacion",
            "tipo_vinculacion_nombre", "apoyo_economico", "cupos", "fecha_inicio", "duracion_meses", "fecha_cierre",
            "estado", "estado_nombre", "observacion_revision", "motivo_cierre", "motivo_cierre_nombre", "publicada_en",
            "programas", "programas_detalle", "habilidades", "habilidades_detalle", "creada_por_nombre",
            "creada_por_oficina", "acciones", "postulantes", "para_estudiante", "creado_en", "actualizado_en",
        ]
        read_only_fields = ["estado", "observacion_revision", "motivo_cierre", "publicada_en"]

    def get_programas_detalle(self, convocatoria):
        return [{"id": p.id, "nombre": p.nombre} for p in convocatoria.programas.all()]

    def get_habilidades_detalle(self, convocatoria):
        return [{"id": h.id, "nombre": h.nombre} for h in convocatoria.habilidades.all()]

    def get_creada_por_oficina(self, convocatoria):
        return convocatoria.creada_por.rol in servicios.ROLES_OFICINA

    def get_acciones(self, convocatoria):
        usuario = self.context["request"].user
        if usuario.rol == Rol.ESTUDIANTE:
            return []
        return servicios.acciones_permitidas(convocatoria, usuario)

    def get_postulantes(self, convocatoria):
        return getattr(convocatoria, "num_postulaciones", None)

    def get_para_estudiante(self, convocatoria):
        """Solo para estudiantes: afinidad (RF-42), su postulación y si puede postularse (RN-04 a RN-08)."""
        datos = self.context.get("estudiante")
        if datos is None:
            return None
        postulacion = datos["postulaciones"].get(convocatoria.pk)
        calculo = afinidad.calcular(datos["perfil"], convocatoria, datos["habilidades"])
        motivo = datos["motivo_perfil"] or servicios_postulacion.motivo_convocatoria(datos["perfil"], convocatoria, postulacion is not None)
        return {
            "afinidad": calculo,
            "guardada": convocatoria.pk in datos["guardadas"],
            "postulacion": {"id": postulacion.pk, "estado": postulacion.estado, "estado_nombre": postulacion.get_estado_display()}
            if postulacion else None,
            "puede_postularse": motivo is None,
            "motivo_no_postular": motivo,
        }

    def validate_fecha_cierre(self, valor):
        if valor < timezone.localdate():
            raise serializers.ValidationError("La fecha de cierre no puede estar en el pasado.")
        return valor

    def validate(self, datos):
        usuario = self.context["request"].user
        actual = self.instance

        # La empresa: la del usuario reclutador, o la que elige la oficina (RF-31)
        if usuario.rol == Rol.EMPRESA:
            datos["empresa"] = usuario.vinculo_empresa.empresa
        elif actual is None and not datos.get("empresa"):
            raise serializers.ValidationError({"empresa": "Selecciona la empresa aliada."})
        if actual is None and not datos["empresa"].puede_publicar:
            raise serializers.ValidationError({"empresa": "La empresa no es aliada o no tiene un convenio vigente (RN-02)."})
        if actual is not None and usuario.rol == Rol.EMPRESA:
            datos.pop("empresa")

        modalidad = datos.get("modalidad", getattr(actual, "modalidad", None))
        ciudad = datos.get("ciudad", getattr(actual, "ciudad", None))
        if modalidad != Modalidad.REMOTA and ciudad is None:
            raise serializers.ValidationError({"ciudad": "La ciudad es obligatoria si la práctica no es remota."})
        return datos

    def create(self, datos):
        datos["creada_por"] = self.context["request"].user
        return super().create(datos)
