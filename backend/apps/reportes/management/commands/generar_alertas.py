from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.cuentas.models import Rol, Usuario
from apps.notificaciones.models import Notificacion
from apps.notificaciones.servicios import notificar
from apps.reportes import alertas


class Command(BaseCommand):
    help = "Resume las alertas de seguimiento del día y avisa a la oficina (RF-66). Un aviso por funcionario y por día."

    def handle(self, *args, **opciones):
        resultado = alertas.calcular()
        if resultado["total"] == 0:
            self.stdout.write("Sin alertas de seguimiento.")
            return
        resumen = " · ".join(f"{c['titulo']}: {c['total']}" for c in resultado["categorias"] if c["total"])
        hoy = timezone.localdate()
        avisados = 0
        for funcionario in Usuario.objects.filter(rol=Rol.OFICINA, is_active=True):
            if Notificacion.objects.filter(usuario=funcionario, tipo="ALERTAS_DIARIAS", creado_en__date=hoy).exists():
                continue  # Idempotente: si se ejecuta dos veces el mismo día no repite el aviso
            notificar(funcionario, "ALERTAS_DIARIAS", f"{resultado['total']} alertas de seguimiento", resumen, url="/oficina/alertas")
            avisados += 1
        self.stdout.write(f"Alertas: {resultado['total']} · funcionarios avisados: {avisados}")
