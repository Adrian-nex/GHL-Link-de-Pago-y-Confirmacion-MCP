import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from payments.models import WebhookEvent

print("\n=== ESTADO DE WEBHOOKS ===")
print(f"Pendientes: {WebhookEvent.objects.filter(status='pending').count()}")
print(f"Success: {WebhookEvent.objects.filter(status='success').count()}")
print(f"Failed: {WebhookEvent.objects.filter(status='failed').count()}")

print("\n=== ÚLTIMOS 10 WEBHOOKS ===")
for e in WebhookEvent.objects.all().order_by("-created_at")[:10]:
    print(f"{e.webhook_id}: {e.status} (intentos: {e.attempts}/{e.max_attempts})")
    if e.last_error:
        print(f"  Error: {e.last_error[:100]}")

print("\n=== WEBHOOKS PENDIENTES ===")
pending = WebhookEvent.objects.filter(status="pending")
for e in pending:
    print(f"{e.webhook_id}: {e.status} (intentos: {e.attempts}/{e.max_attempts})")
    if e.last_error:
        print(f"  Error: {e.last_error[:100]}")
