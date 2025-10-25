from django.db import models
from django.utils import timezone


class Payment(models.Model):
    appointment_id = models.CharField(max_length=100)
    contact_id = models.CharField(max_length=100)
    preference_id = models.CharField(max_length=100)
    payment_id = models.CharField(max_length=100, null=True, blank=True, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.appointment_id} - {self.status}"


class WebhookEvent(models.Model):
    """
    🔹 Tabla para almacenar y gestionar eventos de webhooks

    Conceptos clave:
    - Event-driven architecture: Guardamos primero, procesamos después
    - Idempotencia: Evitamos duplicados con webhook_id único
    - Retry policy: Definimos cuántos intentos y con qué estrategia
    """

    # Estados posibles del evento
    STATUS_PENDING = "pending"  # Recién recibido, esperando procesar
    STATUS_PROCESSING = "processing"  # En proceso de ejecución
    STATUS_SUCCESS = "success"  # Procesado exitosamente
    STATUS_FAILED = "failed"  # Falló después de todos los reintentos

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pendiente"),
        (STATUS_PROCESSING, "Procesando"),
        (STATUS_SUCCESS, "Exitoso"),
        (STATUS_FAILED, "Fallido"),
    ]

    # Identificación del webhook
    webhook_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="ID único del webhook (ej: payment_123 o merchant_order_456)",
    )
    webhook_type = models.CharField(
        max_length=50, help_text="Tipo: payment, merchant_order, etc."
    )

    # Datos del evento
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="webhook_events",
        help_text="Pago relacionado (puede ser null si aún no se creó)",
    )
    mp_payment_id = models.CharField(
        max_length=100, null=True, blank=True, help_text="ID del pago de MercadoPago"
    )
    preference_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="ID de preferencia de MercadoPago",
    )

    # Payload completo del webhook (para debugging y reintentos)
    raw_payload = models.JSONField(help_text="Payload completo recibido del webhook")

    # Control de procesamiento
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True
    )
    processed = models.BooleanField(
        default=False, db_index=True, help_text="True si se procesó exitosamente"
    )
    attempts = models.IntegerField(
        default=0, help_text="Número de intentos de procesamiento"
    )
    max_attempts = models.IntegerField(
        default=3, help_text="Máximo de reintentos antes de marcar como fallido"
    )

    # Información de errores
    last_error = models.TextField(
        null=True, blank=True, help_text="Último error encontrado"
    )
    error_details = models.JSONField(
        null=True, blank=True, help_text="Detalles completos del error"
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True, help_text="Cuándo se recibió el webhook"
    )
    updated_at = models.DateTimeField(auto_now=True, help_text="Última actualización")
    processed_at = models.DateTimeField(
        null=True, blank=True, help_text="Cuándo se procesó exitosamente"
    )
    next_retry_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Cuándo debe intentarse el próximo reintento",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Evento de Webhook"
        verbose_name_plural = "Eventos de Webhook"
        indexes = [
            models.Index(fields=["status", "processed"]),
            models.Index(fields=["next_retry_at"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.webhook_type} - {self.webhook_id} ({self.status})"

    def mark_processing(self):
        """Marcar como en proceso"""
        self.status = self.STATUS_PROCESSING
        self.attempts += 1
        self.save(update_fields=["status", "attempts", "updated_at"])

    def mark_success(self):
        """Marcar como exitoso"""
        self.status = self.STATUS_SUCCESS
        self.processed = True
        self.processed_at = timezone.now()
        self.last_error = None
        self.next_retry_at = None
        self.save(
            update_fields=[
                "status",
                "processed",
                "processed_at",
                "last_error",
                "next_retry_at",
                "updated_at",
            ]
        )

    def mark_failed(self, error_message, error_details=None):
        """Marcar como fallido y programar reintento si corresponde"""
        self.last_error = error_message
        if error_details:
            self.error_details = error_details

        # Si aún quedan intentos, programar reintento
        if self.attempts < self.max_attempts:
            # Estrategia de backoff exponencial: 1min, 5min, 15min
            retry_delays = [60, 300, 900]  # segundos
            delay = retry_delays[min(self.attempts - 1, len(retry_delays) - 1)]
            self.next_retry_at = timezone.now() + timezone.timedelta(seconds=delay)
            self.status = self.STATUS_PENDING
        else:
            # Ya no hay más intentos, marcar como fallido permanentemente
            self.status = self.STATUS_FAILED
            self.next_retry_at = None

        self.save(
            update_fields=[
                "status",
                "last_error",
                "error_details",
                "next_retry_at",
                "updated_at",
            ]
        )
