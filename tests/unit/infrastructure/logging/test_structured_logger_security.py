"""
Testes de segurança para StructuredLogger
"""
import pytest

from src.infrastructure.logging.structured_logger import StructuredLogger


class TestStructuredLoggerSecurity:
    """Testes de segurança para o logger estruturado"""

    def setup_method(self):
        """Setup para cada teste"""
        self.logger = StructuredLogger("test_security")

    def test_sanitize_input_removes_newlines(self):
        """Testa se caracteres de nova linha são escapados"""
        malicious_input = "test\ninjection\rhere"
        result = self.logger._sanitize_input(malicious_input)

        assert "\\n" in result
        assert "\\r" in result
        assert "\n" not in result
        assert "\r" not in result

    def test_sanitize_input_escapes_html(self):
        """Testa se HTML é escapado"""
        malicious_input = "<script>alert('xss')</script>"
        result = self.logger._sanitize_input(malicious_input)

        assert "&lt;" in result
        assert "&gt;" in result
        assert "<script>" not in result

    def test_sanitize_input_handles_non_string(self):
        """Testa se valores não-string são convertidos"""
        result = self.logger._sanitize_input(123)
        assert result == "123"

        result = self.logger._sanitize_input(None)
        assert result == "None"

    def test_format_message_sanitizes_context(self):
        """Testa se o contexto é sanitizado"""
        message = "Test message"
        context = {
            "user": "admin\ninjection",
            "data": "<script>alert('xss')</script>"
        }

        result = self.logger._format_message(message, context)

        assert "\\n" in result
        assert "&lt;" in result
        assert "\n" not in result
        assert "<script>" not in result
