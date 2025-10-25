"""
Tests básicos para el modelo Payment
"""

from django.test import TestCase

from payments.models import Payment, WebhookEvent


class PaymentModelTest(TestCase):
    """Pruebas básicas para el modelo Payment"""

    def test_payment_creation(self):
        """Prueba la creación de un pago"""
        payment = Payment.objects.create(
            appointment_id="Cita_001",
            contact_id="contact_123",
            preference_id="pref_456",
            payment_id="123456789",
            amount=100.50,
            status="pending",
        )

        self.assertEqual(payment.payment_id, "123456789")
        self.assertEqual(payment.status, "pending")
        self.assertEqual(payment.amount, 100.50)

    def test_payment_str_representation(self):
        """Prueba la representación string del pago"""
        payment = Payment.objects.create(
            appointment_id="Cita_001",
            contact_id="contact_123",
            preference_id="pref_456",
            payment_id="123456789",
            amount=100.50,
            status="pending",
        )
        expected_str = f"{payment.appointment_id} - {payment.status}"
        self.assertEqual(str(payment), expected_str)


class WebhookEventModelTest(TestCase):
    """Pruebas básicas para el modelo WebhookEvent"""

    def test_webhook_event_creation(self):
        """Prueba la creación de un evento webhook"""
        webhook = WebhookEvent.objects.create(
            webhook_id="webhook_123",
            webhook_type="payment",
            mp_payment_id="123456789",
            raw_payload={"test": "data"},
            processed=False,
            attempts=0,
        )

        self.assertEqual(webhook.webhook_id, "webhook_123")
        self.assertEqual(webhook.webhook_type, "payment")
        self.assertEqual(webhook.mp_payment_id, "123456789")
