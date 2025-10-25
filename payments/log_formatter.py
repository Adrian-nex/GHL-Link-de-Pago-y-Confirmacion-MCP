"""
Formatter personalizado para logs con colores y emojis
"""

import logging


class ColoredFormatter(logging.Formatter):
    """
    Formatter con colores ANSI y emojis para mejor visualización
    """

    # Códigos de color ANSI
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Verde
        "WARNING": "\033[33m",  # Amarillo
        "ERROR": "\033[31m",  # Rojo
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
        "BOLD": "\033[1m",  # Negrita
        "DIM": "\033[2m",  # Tenue
    }

    # Emojis por tipo de log
    EMOJIS = {
        "WEBHOOK": "📨",
        "PAYMENT": "💳",
        "MERCHANT_ORDER": "📦",
        "GHL": "🏢",
        "REQUEST": "➡️ ",
        "RESPONSE": "⬅️ ",
        "WEBHOOK-PROCESSOR": "⚙️ ",
    }

    # Símbolos de estado
    STATUS = {
        "success": "✓",
        "error": "✗",
        "warning": "⚠",
        "processing": "⚡",
        "info": "ℹ",
    }

    def format(self, record):
        # Color según nivel
        level_color = self.COLORS.get(record.levelname, "")
        reset = self.COLORS["RESET"]
        bold = self.COLORS["BOLD"]
        dim = self.COLORS["DIM"]

        # Formatear timestamp
        timestamp = self.formatTime(record, "%H:%M:%S")

        # Extraer el tipo de log del mensaje
        message = record.getMessage()

        # Detectar tipo de log y agregar emoji
        emoji = ""
        for key, icon in self.EMOJIS.items():
            if f"[{key}]" in message:
                emoji = icon
                break

        # Detectar símbolo de estado en el mensaje
        if "✓" in message or "exitosamente" in message or "guardado" in message:
            status_symbol = self.STATUS["success"]
        elif "✗" in message or "Error" in message or "falló permanentemente" in message:
            status_symbol = self.STATUS["error"]
        elif "⚠" in message or "WARNING" in record.levelname or "falló" in message:
            status_symbol = self.STATUS["warning"]
        elif "⚡" in message or "Procesando" in message:
            status_symbol = self.STATUS["processing"]
        else:
            status_symbol = ""

        # Construir log formateado
        if record.levelname == "INFO":
            # INFO: Verde con emoji
            formatted = f"{dim}[{timestamp}]{reset} {emoji} {message}"
        elif record.levelname == "WARNING":
            # WARNING: Amarillo con advertencia
            formatted = (
                f"{dim}[{timestamp}]{reset} {self.COLORS['WARNING']}⚠️  {message}{reset}"
            )
        elif record.levelname == "ERROR":
            # ERROR: Rojo con X
            formatted = (
                f"{dim}[{timestamp}]{reset} {self.COLORS['ERROR']}✗ {message}{reset}"
            )
        elif record.levelname == "DEBUG":
            # DEBUG: Cyan tenue
            formatted = f"{dim}[{timestamp}] 🔍 {message}{reset}"
        else:
            # Otros: Sin color
            formatted = f"[{timestamp}] {message}"

        return formatted


class FileFormatter(logging.Formatter):
    """
    Formatter para archivo (sin colores ANSI, con emojis)
    """

    def format(self, record):
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")
        level = record.levelname.ljust(8)
        message = record.getMessage()

        # Agregar emojis según contenido
        if "guardado" in message or "exitosamente" in message:
            prefix = "✓"
        elif "Error" in message or "falló permanentemente" in message:
            prefix = "✗"
        elif "WARNING" in record.levelname or "falló" in message:
            prefix = "⚠"
        elif "Procesando" in message:
            prefix = "⚡"
        else:
            prefix = "ℹ"

        return f"[{timestamp}] {level} {prefix} {message}"
