"""Bucle de tareas periódicas del contenedor `scheduler` (arquitectura 3.8). Sin Celery ni Redis."""

import time

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError, ProgrammingError
from django.utils import timezone

INTERVALO_SEGUNDOS = 15 * 60
TAREAS_FRECUENTES = ["cerrar_convocatorias"]
TAREAS_DIARIAS = ["revisar_convenios", "iniciar_practicas", "generar_alertas"]


class Command(BaseCommand):
    help = "Ejecuta las tareas programadas cada 15 minutos y una vez al día."

    def handle(self, *args, **opciones):
        ultimo_dia = None
        self.stdout.write("[scheduler] Iniciado")
        while True:
            try:
                for tarea in TAREAS_FRECUENTES:
                    call_command(tarea)
                hoy = timezone.localdate()
                if hoy != ultimo_dia:
                    for tarea in TAREAS_DIARIAS:
                        call_command(tarea)
                    ultimo_dia = hoy
            except (OperationalError, ProgrammingError) as error:
                # La base de datos aún no está lista o faltan migraciones: se reintenta en el próximo ciclo
                self.stdout.write(f"[scheduler] Base de datos no disponible todavía: {error.__class__.__name__}")
                ultimo_dia = None
            finally:
                connection.close()
            time.sleep(INTERVALO_SEGUNDOS if ultimo_dia else 30)
