"""
Tests básicos para las vistas de webhooks
"""

import json

from django.test import Client, TestCase
from django.urls import reverse


class WebhookViewTest(TestCase):
    """Pruebas básicas para las vistas de webhook"""

    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.client = Client()
        self.webhook_url = "/webhooks/mp"

    def test_webhook_payment_post(self):
        """Prueba el endpoint de webhook para pagos"""
        webhook_data = {"resource": "123456789", "topic": "payment"}

        response = self.client.post(
            self.webhook_url,
            data=json.dumps(webhook_data),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn("status", response_data)
        self.assertEqual(response_data["status"], "received")

    def test_webhook_invalid_json(self):
        """Prueba el endpoint con JSON inválido"""
        response = self.client.post(
            self.webhook_url, data="invalid json", content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
