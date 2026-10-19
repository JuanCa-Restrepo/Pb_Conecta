from django.core.management.base import BaseCommand

from apps.convocatorias.servicios import cerrar_vencidas


class Command(BaseCommand):
    help = "Cierra las convocatorias vencidas o con todos sus cupos legalizados (RN-09)."

    def handle(self, *args, **opciones):
        self.stdout.write(f"Convocatorias cerradas: {cerrar_vencidas()}")
