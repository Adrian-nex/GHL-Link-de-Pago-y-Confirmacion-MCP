import json
import logging
import os

import requests
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Payment
from .services import add_tag_to_contact, get_contacts

# Configurar logging
logger = logging.getLogger(__name__)


def home(request):
    """Vista principal del frontend"""
    return render(request, "payments/index.html")


def get_contacts_view(request):
    """API endpoint para obtener contactos de GHL"""
    try:
        result = get_contacts(limit=100)
        return JsonResponse(result)
    except Exception as e:
        logger.error(f"Error obteniendo contactos: {str(e)}")
        return JsonResponse(
            {"success": False, "contacts": [], "message": f"Error: {str(e)}"},
            status=500,
        )


def get_webhook_events(request):
    """API endpoint para obtener el historial de eventos de webhooks"""
    try:
        from .models import WebhookEvent

        # Obtener parámetros de filtro
        status_filter = request.GET.get("status")
        webhook_type = request.GET.get("type")
        limit = int(request.GET.get("limit", 50))

        # Construir query
        events = WebhookEvent.objects.all()

        if status_filter:
            events = events.filter(status=status_filter)
        if webhook_type:
            events = events.filter(webhook_type=webhook_type)

        events = events.order_by("-created_at")[:limit]

        events_list = []
        for event in events:
            events_list.append(
                {
                    "id": event.id,
                    "webhook_id": event.webhook_id,
                    "webhook_type": event.webhook_type,
                    "status": event.status,
                    "status_display": event.get_status_display(),
                    "processed": event.processed,
                    "attempts": event.attempts,
                    "max_attempts": event.max_attempts,
                    "mp_payment_id": event.mp_payment_id,
                    "preference_id": event.preference_id,
                    "payment_appointment_id": (
                        event.payment.appointment_id if event.payment else None
                    ),
                    "last_error": event.last_error,
                    "created_at": event.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "processed_at": (
                        event.processed_at.strftime("%Y-%m-%d %H:%M:%S")
                        if event.processed_at
                        else None
                    ),
                    "next_retry_at": (
                        event.next_retry_at.strftime("%Y-%m-%d %H:%M:%S")
                        if event.next_retry_at
                        else None
                    ),
                }
            )

        return JsonResponse(
            {"success": True, "events": events_list, "total": len(events_list)}
        )
    except Exception as e:
        logger.error(f"Error obteniendo eventos de webhooks: {str(e)}")
        return JsonResponse(
            {"success": False, "events": [], "message": f"Error: {str(e)}"}, status=500
        )


def get_payments_history(request):
    """API endpoint para obtener el historial de pagos"""
    try:
        from .services import get_contacts

        # Obtener todos los pagos ordenados por fecha de creación (más recientes primero)
        payments = Payment.objects.all().order_by("-created_at")

        # Obtener contactos de GHL para mostrar nombres (máximo 100)
        contacts_result = get_contacts(limit=100)
        contacts_dict = {}
        if contacts_result.get("success"):
            contacts_dict = {
                c["id"]: c["name"] for c in contacts_result.get("contacts", [])
            }

        payments_list = []
        for payment in payments:
            contact_name = contacts_dict.get(
                payment.contact_id, payment.contact_id[:20]
            )

            # Generar init_point para pagos pendientes
            init_point = None
            if payment.status == "pending" and payment.preference_id:
                init_point = f"https://www.mercadopago.com.pe/checkout/v1/redirect?pref_id={payment.preference_id}"

            payments_list.append(
                {
                    "id": payment.id,
                    "appointment_id": payment.appointment_id,
                    "contact_id": payment.contact_id,
                    "contact_name": contact_name,
                    "preference_id": payment.preference_id,
                    "payment_id": payment.payment_id,
                    "amount": float(payment.amount),
                    "status": payment.status,
                    "init_point": init_point,
                    "created_at": payment.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        return JsonResponse(
            {"success": True, "payments": payments_list, "total": len(payments_list)}
        )
    except Exception as e:
        logger.error(f"Error obteniendo historial de pagos: {str(e)}")
        return JsonResponse(
            {"success": False, "payments": [], "message": f"Error: {str(e)}"},
            status=500,
        )


def get_next_appointment_id(request):
    """API endpoint para generar el siguiente ID de cita"""
    try:
        # Obtener el último pago con ID que comience con 'Cita_N'
        last_payment = (
            Payment.objects.filter(appointment_id__startswith="Cita_N")
            .order_by("-created_at")
            .first()
        )

        if last_payment:
            # Extraer el número del último ID (ej: Cita_N011 -> 11)
            last_id = last_payment.appointment_id
            try:
                number = int(last_id.replace("Cita_N", ""))
                next_number = number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1

        # Generar el nuevo ID con formato Cita_NXXX
        next_id = f"Cita_N{next_number:03d}"

        return JsonResponse({"success": True, "next_id": next_id})
    except Exception as e:
        logger.error(f"Error generando siguiente ID: {str(e)}")
        return JsonResponse(
            {"success": False, "next_id": "Cita_N001", "message": f"Error: {str(e)}"},
            status=500,
        )


@csrf_exempt
@require_POST
def create_payment(request):
    try:
        data = json.loads(request.body)
        # Validar campos requeridos
        required_fields = ["appointmentId", "contactId", "amount"]
        for field in required_fields:
            if field not in data:
                error_msg = f"Campo requerido faltante: {field}"
                logger.error(error_msg)
                return JsonResponse({"error": error_msg}, status=400)
        appointment_id = data["appointmentId"]
        contact_id = data["contactId"]
        amount = float(data["amount"])
        description = data.get("description", "Cita ReflexoPerú")
        if amount <= 0:
            error_msg = "El monto debe ser mayor a 0"
            logger.error(error_msg)
            return JsonResponse({"error": error_msg}, status=400)
        existing_payment = Payment.objects.filter(appointment_id=appointment_id).first()
        if existing_payment:
            if existing_payment.status == "approved":
                return JsonResponse(
                    {
                        "error": "Ya existe un pago aprobado para esta cita",
                        "existing_payment": {
                            "id": existing_payment.id,
                            "status": existing_payment.status,
                            "payment_id": existing_payment.payment_id,
                        },
                    },
                    status=400,
                )
            elif existing_payment.status == "pending":
                return JsonResponse(
                    {
                        "error": "Ya existe un pago pendiente para esta cita",
                        "existing_payment": {
                            "id": existing_payment.id,
                            "status": existing_payment.status,
                            "preference_id": existing_payment.preference_id,
                        },
                    },
                    status=400,
                )
        payload = {
            "items": [
                {
                    "title": description,
                    "quantity": 1,
                    "unit_price": amount,
                    "currency_id": "PEN",
                }
            ],
            "external_reference": appointment_id,
            "notification_url": f"{settings.BASE_URL}/webhooks/mp",
            "back_urls": {
                "success": f"{settings.BASE_URL}/?status=success",
                "failure": f"{settings.BASE_URL}/?status=failure",
                "pending": f"{settings.BASE_URL}/?status=pending",
            },
            "auto_return": "approved",
            "statement_descriptor": "ReflexoPeru",
            "payment_methods": {"installments": 1},
        }
        headers = {
            "Authorization": f"Bearer {settings.MP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        }
        response = requests.post(
            "https://api.mercadopago.com/checkout/preferences",
            headers=headers,
            data=json.dumps(payload),
        )
        if response.status_code != 201:
            error_msg = f"No se pudo crear la preferencia. Status: {response.status_code}, Response: {response.text}"
            logger.error(error_msg)
            return JsonResponse(
                {"error": "No se pudo crear la preferencia", "details": response.text},
                status=400,
            )
        pref_data = response.json()
        preference_id = pref_data["id"]
        init_point = pref_data["init_point"]
        payment_obj = Payment.objects.create(
            appointment_id=appointment_id,
            contact_id=contact_id,
            preference_id=preference_id,
            amount=amount,
            status="pending",
        )
        result = {
            "success": True,
            "init_point": init_point,
            "preference_id": preference_id,
            "payment_id": None,
            "status": "pending",
        }
        return JsonResponse(result)
    except json.JSONDecodeError as e:
        error_msg = f"JSON inválido en el body de la petición: {str(e)}"
        logger.error(error_msg)
        return JsonResponse(
            {"error": "JSON inválido en el body de la petición"}, status=400
        )
    except ValueError as e:
        error_msg = f"Error en los datos: {str(e)}"
        logger.error(error_msg)
        return JsonResponse({"error": error_msg}, status=400)
    except KeyError as e:
        error_msg = f"Campo requerido faltante: {str(e)}"
        logger.error(error_msg)
        return JsonResponse({"error": error_msg}, status=400)
    except Exception as e:
        error_msg = f"Error en create_payment: {e}"
        logger.error(error_msg)
        print(f"Error en create_payment: {e}")
        return JsonResponse({"error": "Error interno del servidor"}, status=500)


@csrf_exempt
def get_payment_status(request, appointment_id):
    """Consultar el estado de un pago por appointment_id"""
    try:
        payment = Payment.objects.filter(appointment_id=appointment_id).first()
        if not payment:
            return JsonResponse(
                {"error": "No se encontró pago para esta cita"}, status=404
            )

        return JsonResponse(
            {
                "appointment_id": payment.appointment_id,
                "contact_id": payment.contact_id,
                "preference_id": payment.preference_id,
                "payment_id": payment.payment_id,
                "amount": float(payment.amount),
                "status": payment.status,
                "created_at": payment.created_at.isoformat(),
            }
        )

    except Exception as e:
        print(f"Error en get_payment_status: {e}")
        return JsonResponse({"error": "Error interno del servidor"}, status=500)


@csrf_exempt
@require_POST
def mp_webhook(request):
    """
    🔹 Endpoint de webhook con arquitectura event-driven

    Estrategia:
    1. ✅ Responder 200 OK inmediatamente (confirmar recepción)
    2. 💾 Guardar evento en BD
    3. ⚡ Procesar de forma asíncrona

    Beneficios:
    - No perdemos webhooks aunque el servidor esté lento
    - MercadoPago no reintenta innecesariamente
    - Podemos reintentar procesamiento en caso de error
    """
    from .models import WebhookEvent
    from .services.webhook_processor import WebhookProcessor

    try:
        # Intentar parsear el body (puede estar vacío para algunos webhooks)
        try:
            payload = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            payload = {}

        # MercadoPago envía los datos en query params Y en el body
        topic = request.GET.get("topic") or payload.get("topic")

        # El resource puede venir en diferentes formatos:
        # 1. En query param 'id'
        # 2. En payload como 'resource'
        # 3. En payload como 'data.id'
        resource_id = request.GET.get("id") or payload.get("resource")

        # Determinar tipo de webhook e ID único
        webhook_type = None
        webhook_id = None
        payment_id = None

        logger.info(f"📨 Webhook recibido | Topic: {topic} | Resource: {resource_id}")

        # Caso 1: merchant_order notification
        if topic == "merchant_order":
            if resource_id:
                # Si viene merchant_orders/123, extraer solo el ID
                if "merchant_orders/" in str(resource_id):
                    merchant_order_id = str(resource_id).split("merchant_orders/")[-1]
                else:
                    merchant_order_id = str(resource_id)

                webhook_type = "merchant_order"
                webhook_id = f"merchant_order_{merchant_order_id}"

        # Caso 2: payment notification
        elif topic == "payment":
            if resource_id:
                payment_id = str(resource_id)
                webhook_type = "payment"
                webhook_id = f"payment_{payment_id}"
            elif payload.get("data", {}).get("id"):
                # Formato alternativo: {"data": {"id": "123"}}
                payment_id = str(payload["data"]["id"])
                webhook_type = "payment"
                webhook_id = f"payment_{payment_id}"

        # Caso 3: Formatos legacy (compatibilidad con código anterior)
        elif (
            payload.get("type") == "payment"
            or payload.get("action") == "payment.created"
        ):
            payment_id = str(payload["data"]["id"])
            webhook_type = "payment"
            webhook_id = f"payment_{payment_id}"

        # Si no identificamos el tipo, rechazar
        if not webhook_type or not webhook_id:
            logger.warning(
                f"📨 ⚠ Webhook no reconocido | Topic: {topic} | Resource: {resource_id}"
            )
            return JsonResponse({"error": "Tipo de webhook no reconocido"}, status=400)

        # 🔹 PASO 1: Verificar si ya existe este evento (idempotencia)
        existing_event = WebhookEvent.objects.filter(webhook_id=webhook_id).first()

        if existing_event:
            # Si ya fue procesado exitosamente, solo confirmar
            if existing_event.processed:
                logger.debug(
                    f"📨 ✓ Webhook duplicado (ya procesado) | ID: {webhook_id}"
                )
                return JsonResponse({"status": "already_processed"})

            # Si está pendiente o falló, lo reprocesaremos más tarde
            logger.info(
                f"📨 ⚡ Webhook existente | ID: {webhook_id} | Intento: {existing_event.attempts}"
            )
            return JsonResponse({"status": "already_received"})

        # 🔹 PASO 2: Guardar el evento en la base de datos
        event = WebhookEvent.objects.create(
            webhook_id=webhook_id,
            webhook_type=webhook_type,
            mp_payment_id=payment_id,
            raw_payload=payload,
            status=WebhookEvent.STATUS_PENDING,
        )

        logger.info(f"📨 ✓ Webhook guardado | ID: {webhook_id} | DB ID: {event.id}")

        # 🔹 PASO 3: Confirmar recepción INMEDIATAMENTE (200 OK)
        # Esto es crítico: debemos responder rápido para que MP no reintente
        response = JsonResponse({"status": "received", "event_id": event.id})

        # 🔹 PASO 4: Procesar de forma asíncrona (después de confirmar)
        # En producción, esto debería ser con Celery o similar
        # Por ahora, lo procesamos en el mismo request (pero después de responder)
        try:
            processor = WebhookProcessor(event)
            processor.process()
        except Exception as e:
            # Si falla el procesamiento, no afecta la respuesta
            # El evento quedará como pendiente y se reintentará después
            logger.error(f"📨 ✗ Error procesando | ID: {webhook_id} | Error: {str(e)}")

        return response

    except json.JSONDecodeError as e:
        logger.error(f"📨 ✗ JSON inválido | Error: {e}")
        return JsonResponse({"error": "JSON inválido"}, status=400)
    except Exception as e:
        logger.error(f"📨 ✗ Error crítico | Error: {e}")
        # Incluso si hay un error, intentamos responder 200
        # para que MP no reintente innecesariamente
        return JsonResponse({"error": str(e)}, status=200)
