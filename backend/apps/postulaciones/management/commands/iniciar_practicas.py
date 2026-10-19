from django.core.management.base import BaseCommand

from apps.postulaciones.practicas import iniciar_practicas


class Command(BaseCommand):
    help = "Pasa a «En curso» las prácticas legalizadas cuya fecha de inicio ya llegó."

    def handle(self, *args, **opciones):
        self.stdout.write(f"Prácticas iniciadas: {iniciar_practicas()}")
