r"""
Comando de Django para procesar webhooks pendientes

Uso:
    python manage.py process_webhooks

Este comando debe ejecutarse periódicamente (ej: cada 1 minuto con cron o Task Scheduler)

En Windows con Task Scheduler:
    - Acción: Iniciar un programa
    - Programa: C:\ruta\a\python.exe
    - Argumentos: manage.py process_webhooks
    - Directorio: C:\Users\Ignacio\Downloads\ghl-payments
    - Desencadenador: Repetir cada 1 minuto
"""

import logging

from django.core.management.base import BaseCommand

from payments.services.webhook_processor import process_pending_webhooks

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Procesa webhooks pendientes con reintentos automáticos"

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Ejecutar una sola vez y salir (útil para cron)",
        )
        parser.add_argument(
            "--loop",
            action="store_true",
            help="Ejecutar en loop infinito cada 60 segundos (útil para desarrollo)",
        )

    def handle(self, *args, **options):
        if options["loop"]:
            self.stdout.write(
                self.style.SUCCESS(
                    "🔄 Modo loop: procesando webhooks cada 60 segundos..."
                )
            )
            self.stdout.write(self.style.WARNING("   Presiona Ctrl+C para detener\n"))

            import time

            try:
                while True:
                    process_pending_webhooks()
                    time.sleep(60)
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING("\n⏹ Detenido por el usuario"))
        else:
            # Modo por defecto: ejecutar una vez
            self.stdout.write("⚡ Procesando webhooks pendientes...")
            process_pending_webhooks()
            self.stdout.write(self.style.SUCCESS("✓ Procesamiento completado"))
