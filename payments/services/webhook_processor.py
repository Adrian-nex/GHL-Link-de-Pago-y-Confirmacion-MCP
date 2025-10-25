"""
🔹 Servicio para procesar eventos de webhooks de forma asíncrona

Conceptos clave:
- Separación de responsabilidades: recepción vs procesamiento
- Idempotencia: Procesamos cada evento una sola vez
- Resilencia: Reintentos automáticos con backoff exponencial
- Observabilidad: Logs detallados de cada paso
"""

import json
import logging

import requests
from django.conf import settings
from django.utils import timezone

from payments.models import Payment, WebhookEvent
from payments.services import add_tag_to_contact

logger = logging.getLogger(__name__)


class WebhookProcessor:
    """
    Procesador de eventos de webhooks con reintentos automáticos
    """

    def __init__(self, event: WebhookEvent):
        self.event = event
        self.mp_headers = {"Authorization": f"Bearer {settings.MP_ACCESS_TOKEN}"}

    def process(self):
        """
        Método principal para procesar un evento

        Returns:
            bool: True si se procesó exitosamente, False si falló
        """
        logger.info(
            f"[WEBHOOK-PROCESSOR] ⚡ Procesando {self.event.webhook_type} | "
            f"ID: {self.event.webhook_id} | Intento: {self.event.attempts + 1}/{self.event.max_attempts}"
        )

        # Marcar como en proceso
        self.event.mark_processing()

        try:
            # Determinar el tipo de webhook y procesarlo
            if self.event.webhook_type == "payment":
                self._process_payment_webhook()
            elif self.event.webhook_type == "merchant_order":
                self._process_merchant_order_webhook()
            else:
                raise ValueError(
                    f"Tipo de webhook desconocido: {self.event.webhook_type}"
                )

            # Si llegamos aquí, el procesamiento fue exitoso
            self.event.mark_success()
            logger.info(f"⚙️ ✓ Evento procesado | ID: {self.event.webhook_id}")
            return True

        except Exception as e:
            # Capturar el error y programar reintento
            error_message = str(e)
            error_details = {
                "error_type": type(e).__name__,
                "error_message": error_message,
                "attempt": self.event.attempts,
            }

            self.event.mark_failed(error_message, error_details)

            if self.event.status == WebhookEvent.STATUS_FAILED:
                logger.error(
                    f"⚙️ ✗ Evento fallido permanentemente | ID: {self.event.webhook_id} | "
                    f"Intentos: {self.event.attempts} | Error: {error_message}"
                )
            else:
                next_retry = self.event.next_retry_at.strftime("%Y-%m-%d %H:%M:%S")
                logger.warning(
                    f"⚙️ ⚠ Reintento programado | ID: {self.event.webhook_id} | "
                    f"Intento: {self.event.attempts} | Próximo: {next_retry} | Error: {error_message}"
                )

            return False

    def _process_payment_webhook(self):
        """Procesar webhook de tipo 'payment'"""
        payment_id = self.event.mp_payment_id

        if not payment_id:
            raise ValueError("payment_id no encontrado en el evento")

        logger.info(f"💳 ➡️ Consultando MP | Payment ID: {payment_id}")

        # Consultar detalles del pago a MercadoPago
        response = requests.get(
            f"https://api.mercadopago.com/v1/payments/{payment_id}",
            headers=self.mp_headers,
            timeout=10,
        )

        if response.status_code != 200:
            raise Exception(
                f"Error al consultar pago {payment_id}: Status {response.status_code}"
            )

        payment_data = response.json()
        status = payment_data.get("status")
        preference_id = payment_data.get("preference_id")
        external_reference = payment_data.get("external_reference")
        transaction_amount = payment_data.get("transaction_amount", 0)
        payer_email = payment_data.get("payer", {}).get("email", "unknown")

        logger.info(
            f"💳 ⬅️ Respuesta MP | Status: {status} | Monto: ${transaction_amount} | Email: {payer_email}"
        )
        logger.info(
            f"💳 IDs | preference_id: {preference_id} | external_reference: {external_reference}"
        )

        # Buscar el pago en nuestra BD
        payment = None

        # Intento 1: Buscar por preference_id (si existe)
        if preference_id:
            payment = Payment.objects.filter(preference_id=preference_id).first()
            if payment:
                logger.info(f"💳 ✓ Encontrado por preference_id: {preference_id}")

        # Intento 2: Buscar por external_reference (appointment_id)
        if not payment and external_reference:
            payment = Payment.objects.filter(appointment_id=external_reference).first()
            if payment:
                logger.info(
                    f"💳 ✓ Encontrado por external_reference: {external_reference}"
                )
                # Actualizar el preference_id si no lo tiene
                if not payment.preference_id and preference_id:
                    payment.preference_id = preference_id

        # Intento 3: Buscar por payment_id (si ya fue procesado antes)
        if not payment:
            payment = Payment.objects.filter(payment_id=payment_id).first()
            if payment:
                logger.info(f"💳 ✓ Encontrado por payment_id: {payment_id}")

        if not payment:
            error_msg = f"No se encontró pago en BD. preference_id: {preference_id}, external_reference: {external_reference}, payment_id: {payment_id}"
            logger.error(f"💳 ✗ {error_msg}")
            raise Exception(error_msg)

        # Solo actualizar si hay cambios
        if payment.payment_id != payment_id or payment.status != status:
            payment.payment_id = payment_id
            payment.status = status
            payment.save()
            logger.info(
                f"💳 ✓ Actualizado | Payment ID: {payment_id} → Status: {status}"
            )

            # Asociar el evento con el pago
            self.event.payment = payment
            if preference_id:
                self.event.preference_id = preference_id
            self.event.save(update_fields=["payment", "preference_id"])

            # Si el pago fue aprobado, actualizar GHL
            if status == "approved":
                self._add_ghl_tag(payment.contact_id)
        else:
            logger.info(f"💳 Sin cambios | Payment ID: {payment_id}")

    def _process_merchant_order_webhook(self):
        """Procesar webhook de tipo 'merchant_order'"""
        merchant_order_id = self.event.webhook_id.split("_")[-1]

        logger.info(f"📦 ➡️ Consultando orden | ID: {merchant_order_id}")

        # Consultar detalles de la orden
        response = requests.get(
            f"https://api.mercadopago.com/merchant_orders/{merchant_order_id}",
            headers=self.mp_headers,
            timeout=10,
        )

        if response.status_code != 200:
            raise Exception(
                f"Error al consultar orden {merchant_order_id}: Status {response.status_code}"
            )

        order_data = response.json()
        preference_id = order_data.get("preference_id")
        payments = order_data.get("payments", [])
        total_amount = order_data.get("total_amount", 0)
        order_status = order_data.get("order_status", "unknown")

        logger.info(
            f"📦 ⬅️ Respuesta MP | Status: {order_status} | Monto: ${total_amount} | Pagos: {len(payments)}"
        )

        # Procesar cada pago en la orden
        if preference_id:
            payment = Payment.objects.filter(preference_id=preference_id).first()

            if not payment:
                raise Exception(
                    f"No se encontró pago con preference_id: {preference_id}"
                )

            has_changes = False

            for payment_info in payments:
                payment_id = str(payment_info.get("id"))
                status = payment_info.get("status")

                # Solo actualizar si es un payment_id nuevo
                if payment_id and (
                    not payment.payment_id or payment.payment_id != payment_id
                ):
                    payment.payment_id = payment_id
                    payment.status = status
                    payment.save()
                    has_changes = True

                    logger.info(
                        f"📦 ✓ Pago actualizado | ID: {payment_id} → Status: {status}"
                    )

                    # Asociar el evento con el pago
                    self.event.payment = payment
                    self.event.mp_payment_id = payment_id
                    self.event.preference_id = preference_id
                    self.event.save(
                        update_fields=["payment", "mp_payment_id", "preference_id"]
                    )

                    # Si el pago fue aprobado, actualizar GHL
                    if status == "approved":
                        self._add_ghl_tag(payment.contact_id)

            if not has_changes:
                logger.info(f"📦 Sin cambios | Orden: {merchant_order_id}")
        else:
            logger.warning(
                f"📦 ⚠ preference_id no encontrado | Orden: {merchant_order_id}"
            )

    def _add_ghl_tag(self, contact_id):
        """Agregar tag a contacto en GoHighLevel"""
        logger.info(f"🏢 ➡️ Agregando tag | Contact ID: {contact_id}")

        try:
            result = add_tag_to_contact(contact_id, "pago_confirmado")

            if result.get("success"):
                logger.info(f"🏢 ✓ Tag agregado | {result.get('message')}")
            else:
                # No lanzar excepción aquí, solo logueamos el error
                # El webhook se considera exitoso aunque GHL falle
                logger.error(f"🏢 ✗ Error agregando tag | {result.get('message')}")
        except Exception as e:
            # No lanzar excepción aquí, solo logueamos el error
            logger.error(f"🏢 ✗ Excepción agregando tag | {str(e)}")


def process_pending_webhooks():
    """
    Procesar todos los webhooks pendientes que estén listos para reintento

    Este método debe ser llamado periódicamente (ej: cada 1 minuto con cron)
    """
    now = timezone.now()

    # Buscar eventos pendientes que:
    # 1. Estén en estado pending
    # 2. No tengan next_retry_at (primera vez) O ya haya pasado el tiempo de espera
    pending_events = (
        WebhookEvent.objects.filter(status=WebhookEvent.STATUS_PENDING, processed=False)
        .filter(models.Q(next_retry_at__isnull=True) | models.Q(next_retry_at__lte=now))
        .order_by("created_at")[:10]
    )  # Procesar máximo 10 eventos por vez

    if not pending_events:
        logger.debug("⚙️ No hay eventos pendientes")
        return

    logger.info(f"⚙️ ⚡ Procesando lote | Eventos: {len(pending_events)}")

    success_count = 0
    failed_count = 0

    for event in pending_events:
        processor = WebhookProcessor(event)
        if processor.process():
            success_count += 1
        else:
            failed_count += 1

    logger.info(
        f"⚙️ Resultado | ✓ Exitosos: {success_count} | ✗ Fallidos: {failed_count}"
    )


# Importar Q para las queries
from django.db import models
