from django.core.management.base import BaseCommand

from apps.empresas.servicios import revisar_convenios


class Command(BaseCommand):
    help = "Marca empresas con convenio vencido y avisa de convenios próximos a vencer (RF-26)."

    def handle(self, *args, **opciones):
        self.stdout.write(f"Empresas con convenio vencido: {revisar_convenios()}")
