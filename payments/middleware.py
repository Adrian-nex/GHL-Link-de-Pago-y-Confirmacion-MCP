"""
Middleware personalizado para la aplicación de pagos
"""

import logging

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """
    Middleware para registrar información de las peticiones HTTP con formato mejorado
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Código antes de que se procese la vista
        method = request.method
        path = request.path

        # Solo loguear ciertos endpoints importantes
        if "/webhooks/" in path or "/api/" in path:
            # Formatear el log de entrada
            if method == "POST":
                logger.info(f"[REQUEST] 📥 {method} {path}")
            elif method == "GET":
                logger.info(f"[REQUEST] 📤 {method} {path}")
            else:
                logger.info(f"[REQUEST] {method} {path}")

        # Procesar la petición
        response = self.get_response(request)

        # Código después de que se procese la vista
        if "/webhooks/" in path or "/api/" in path:
            # Colorear según status code
            status = response.status_code
            if 200 <= status < 300:
                status_icon = "✓"
            elif 400 <= status < 500:
                status_icon = "⚠"
            else:
                status_icon = "✗"

            logger.info(f"[RESPONSE] {status_icon} {method} {path} → {status}")

        return response
