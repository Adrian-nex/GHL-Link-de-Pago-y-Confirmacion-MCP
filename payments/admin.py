from django.contrib import admin
from django.utils.html import format_html

from .models import Payment, WebhookEvent


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "appointment_id",
        "contact_id",
        "amount",
        "status",
        "payment_id",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("appointment_id", "contact_id", "payment_id", "preference_id")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = (
        "webhook_id",
        "webhook_type",
        "status_badge",
        "attempts",
        "payment_link",
        "created_at",
        "next_retry_at",
    )
    list_filter = ("status", "webhook_type", "processed", "created_at")
    search_fields = ("webhook_id", "mp_payment_id", "preference_id")
    readonly_fields = (
        "webhook_id",
        "webhook_type",
        "raw_payload",
        "created_at",
        "updated_at",
        "processed_at",
        "error_details",
    )
    ordering = ("-created_at",)

    fieldsets = (
        ("Identificación", {"fields": ("webhook_id", "webhook_type", "created_at")}),
        ("Relaciones", {"fields": ("payment", "mp_payment_id", "preference_id")}),
        ("Estado", {"fields": ("status", "processed", "attempts", "max_attempts")}),
        ("Timestamps", {"fields": ("updated_at", "processed_at", "next_retry_at")}),
        ("Datos", {"fields": ("raw_payload",), "classes": ("collapse",)}),
        (
            "Errores",
            {"fields": ("last_error", "error_details"), "classes": ("collapse",)},
        ),
    )

    def status_badge(self, obj):
        """Mostrar badge de color según el estado"""
        colors = {
            "pending": "#ffc107",  # amarillo
            "processing": "#2196f3",  # azul
            "success": "#4caf50",  # verde
            "failed": "#f44336",  # rojo
        }
        color = colors.get(obj.status, "#999")
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )

    status_badge.short_description = "Estado"

    def payment_link(self, obj):
        """Mostrar link al pago relacionado"""
        if obj.payment:
            url = f"/admin/payments/payment/{obj.payment.id}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.payment.appointment_id)
        return "-"

    payment_link.short_description = "Pago"

    actions = ["retry_failed_events"]

    def retry_failed_events(self, request, queryset):
        """Acción para reintentar eventos fallidos"""
        from django.utils import timezone

        count = 0
        for event in queryset.filter(status__in=["failed", "pending"]):
            event.status = WebhookEvent.STATUS_PENDING
            event.next_retry_at = timezone.now()
            event.save(update_fields=["status", "next_retry_at"])
            count += 1

        self.message_user(request, f"{count} eventos programados para reintento")

    retry_failed_events.short_description = "Reintentar eventos seleccionados"
