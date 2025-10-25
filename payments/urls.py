from django.urls import path

from .views import (
    create_payment,
    get_contacts_view,
    get_next_appointment_id,
    get_payment_status,
    get_payments_history,
    get_webhook_events,
    home,
    mp_webhook,
)

urlpatterns = [
    path("", home, name="home"),
    path("api/contacts", get_contacts_view, name="get_contacts"),
    path("api/payments", get_payments_history, name="payments_history"),
    path("api/webhook-events", get_webhook_events, name="webhook_events"),
    path(
        "api/next-appointment-id", get_next_appointment_id, name="next_appointment_id"
    ),
    path("api/create-payment", create_payment, name="create_payment"),
    path("payments/status/<str:appointment_id>", get_payment_status),
    path("webhooks/mp", mp_webhook),
]
