"""
Logger estruturado para o PythonSearchApp
"""
import logging
import sys
import html
from typing import Any


class StructuredLogger:
    """Logger estruturado com contexto e níveis apropriados"""

    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Evita duplicação de handlers
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '[%(levelname)s] %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log de informação com contexto opcional"""
        formatted_msg = self._format_message(self._sanitize_input(message), kwargs)
        self.logger.info(formatted_msg)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log de erro com contexto opcional"""
        formatted_msg = self._format_message(self._sanitize_input(message), kwargs)
        self.logger.error(formatted_msg)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log de aviso com contexto opcional"""
        formatted_msg = self._format_message(self._sanitize_input(message), kwargs)
        self.logger.warning(formatted_msg)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log de debug com contexto opcional"""
        formatted_msg = self._format_message(self._sanitize_input(message), kwargs)
        self.logger.debug(formatted_msg)

    def _sanitize_input(self, value: Any) -> str:
        """Sanitiza entrada para prevenir log injection"""
        if isinstance(value, str):
            # Remove caracteres de controle e escape HTML
            sanitized = value.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
            return html.escape(sanitized)
        return str(value)

    def _format_message(self, message: str, context: dict) -> str:
        """Formata mensagem com contexto estruturado"""
        sanitized_message = message  # Já sanitizado nos métodos públicos

        if not context:
            return sanitized_message

        sanitized_context = {k: self._sanitize_input(v) for k, v in context.items()}
        context_str = " | ".join([f"{k}={v}" for k, v in sanitized_context.items()])
        return f"{sanitized_message} | {context_str}"
