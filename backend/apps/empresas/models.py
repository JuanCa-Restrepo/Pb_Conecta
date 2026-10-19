from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.catalogos.models import Ciudad, Sector
from apps.comun.modelos import RutaAleatoria, ck_opciones


class EmpresaTamano(models.TextChoices):
    MICRO = "MICRO", "Microempresa"
    PEQUENA = "PEQUENA", "Pequeña"
    MEDIANA = "MEDIANA", "Mediana"
    GRANDE = "GRANDE", "Grande"


class EmpresaEstado(models.TextChoices):
    PENDIENTE = "PENDIENTE", "Pendiente de aprobación"
    ALIADA = "ALIADA", "Aliada"
    RECHAZADA = "RECHAZADA", "Rechazada"
    CONVENIO_VENCIDO = "CONVENIO_VENCIDO", "Convenio vencido"
    SUSPENDIDA = "SUSPENDIDA", "Suspendida"


class Empresa(models.Model):
    Tamano = EmpresaTamano
    Estado = EmpresaEstado

    razon_social = models.CharField(max_length=200)
    nit = models.CharField("NIT", max_length=15, unique=True)
    sector = models.ForeignKey(Sector, on_delete=models.PROTECT)
    tamano = models.CharField("tamaño", max_length=25, choices=Tamano.choices, null=True, blank=True)
    descripcion = models.TextField(blank=True)
    logo = models.ImageField(upload_to=RutaAleatoria("publico/logos"), blank=True)
    sitio_web = models.URLField(max_length=300, blank=True)
    ciudad = models.ForeignKey(Ciudad, on_delete=models.PROTECT)
    direccion = models.CharField(max_length=200, blank=True)
    contacto_nombre = models.CharField(max_length=150)
    contacto_email = models.EmailField(max_length=254)
    contacto_telefono = models.CharField(max_length=20, blank=True)
    estado = models.CharField(max_length=25, choices=Estado.choices, default=Estado.PENDIENTE)
    motivo_estado = models.TextField(blank=True)
    creada_por_oficina = models.BooleanField(default=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    seguidores = models.ManyToManyField(
        "estudiantes.PerfilEstudiante", through="EmpresaSeguida", related_name="empresas_seguidas"
    )

    class Meta:
        db_table = "empresa"
        ordering = ["razon_social"]
        indexes = [models.Index(fields=["estado"], name="empresa_estado_idx")]
        constraints = [
            ck_opciones("empresa", "tamano", EmpresaTamano, nulo=True),
            ck_opciones("empresa", "estado", EmpresaEstado),
            models.CheckConstraint(  # RN-11: motivo obligatorio al rechazar o suspender
                condition=~models.Q(estado__in=["RECHAZADA", "SUSPENDIDA"]) | ~models.Q(motivo_estado=""),
                name="empresa_motivo_al_rechazar",
            ),
        ]

    def __str__(self):
        return self.razon_social

    def convenio_vigente(self, fecha=None):
        """Recorre .all() para aprovechar prefetch_related("convenios") en los listados."""
        fecha = fecha or timezone.localdate()
        vigentes = [c for c in self.convenios.all() if c.fecha_inicio <= fecha <= c.fecha_fin]
        return max(vigentes, key=lambda c: c.fecha_fin, default=None)

    @property
    def puede_publicar(self):
        """RN-02: aliada y con convenio vigente."""
        return self.estado == self.Estado.ALIADA and self.convenio_vigente() is not None


class UsuarioEmpresa(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vinculo_empresa")
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="usuarios")
    cargo = models.CharField(max_length=100, blank=True)
    es_principal = models.BooleanField(default=True)

    class Meta:
        db_table = "usuario_empresa"
        verbose_name = "usuario de empresa"
        verbose_name_plural = "usuarios de empresa"


class Convenio(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="convenios")
    numero = models.CharField("número", max_length=50, unique=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    documento = models.FileField(upload_to=RutaAleatoria("protegido/convenios"), blank=True)
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "convenio"
        ordering = ["-fecha_fin"]
        indexes = [models.Index(fields=["empresa", "fecha_fin"], name="convenio_empresa_fin_idx")]
        constraints = [
            models.CheckConstraint(condition=models.Q(fecha_fin__gt=models.F("fecha_inicio")), name="convenio_fechas_validas")
        ]

    def __str__(self):
        return f"{self.numero} · {self.empresa}"


class EmpresaSeguida(models.Model):
    estudiante = models.ForeignKey("estudiantes.PerfilEstudiante", on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "empresa_seguida"
        constraints = [models.UniqueConstraint(fields=["estudiante", "empresa"], name="empresa_seguida_uq")]
