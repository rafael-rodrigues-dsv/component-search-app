"""
Testes unitários para StructuredLogger
"""
import logging
import os
import sys
import unittest

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src.infrastructure.logging.structured_logger import StructuredLogger


class TestStructuredLogger(unittest.TestCase):
    """Testes para StructuredLogger"""

    def setUp(self):
        """Setup para cada teste"""
        # Limpa handlers existentes para evitar interferência
        logging.getLogger().handlers.clear()

    def test_logger_creation_with_default_level(self):
        """Testa criação do logger com nível padrão"""
        logger = StructuredLogger("test_logger")

        self.assertEqual(logger.logger.name, "test_logger")
        self.assertEqual(logger.logger.level, logging.INFO)
        self.assertEqual(len(logger.logger.handlers), 1)

    def test_logger_creation_with_custom_level(self):
        """Testa criação do logger com nível customizado"""
        logger = StructuredLogger("test_logger", logging.DEBUG)

        self.assertEqual(logger.logger.level, logging.DEBUG)

    def test_info_logging_without_context(self):
        """Testa log de info sem contexto"""
        with self.assertLogs(level='INFO') as log:
            logger = StructuredLogger("test_logger")
            logger.info("Test message")

            self.assertEqual(len(log.records), 1)
            self.assertEqual(log.records[0].levelname, 'INFO')
            self.assertIn("Test message", log.records[0].getMessage())

    def test_info_logging_with_context(self):
        """Testa log de info com contexto"""
        with self.assertLogs(level='INFO') as log:
            logger = StructuredLogger("test_logger")
            logger.info("Processing term", term="elevadores", count=5)

            self.assertEqual(len(log.records), 1)
            self.assertEqual(log.records[0].levelname, 'INFO')
            message = log.records[0].getMessage()
            self.assertIn("Processing term", message)
            self.assertIn("term=elevadores", message)
            self.assertIn("count=5", message)

    def test_error_logging_without_context(self):
        """Testa log de erro sem contexto"""
        with self.assertLogs(level='ERROR') as log:
            logger = StructuredLogger("test_logger")
            logger.error("Error occurred")

            self.assertEqual(len(log.records), 1)
            self.assertEqual(log.records[0].levelname, 'ERROR')
            self.assertIn("Error occurred", log.records[0].getMessage())

    def test_error_logging_with_context(self):
        """Testa log de erro com contexto"""
        with self.assertLogs(level='ERROR') as log:
            logger = StructuredLogger("test_logger")
            logger.error("Search failed", term="invalid", attempts=3)

            self.assertEqual(len(log.records), 1)
            self.assertEqual(log.records[0].levelname, 'ERROR')
            message = log.records[0].getMessage()
            self.assertIn("Search failed", message)
            self.assertIn("term=invalid", message)
            self.assertIn("attempts=3", message)

    def test_warning_logging_with_context(self):
        """Testa log de warning com contexto"""
        with self.assertLogs(level='WARNING') as log:
            logger = StructuredLogger("test_logger")
            logger.warning("Outside working hours", start=8, end=22)

            self.assertEqual(len(log.records), 1)
            self.assertEqual(log.records[0].levelname, 'WARNING')
            message = log.records[0].getMessage()
            self.assertIn("Outside working hours", message)
            self.assertIn("start=8", message)
            self.assertIn("end=22", message)

    def test_debug_logging_with_context(self):
        """Testa log de debug com contexto"""
        with self.assertLogs(level='DEBUG') as log:
            logger = StructuredLogger("test_logger", logging.DEBUG)
            logger.debug("Site already visited", domain="example.com")

            self.assertEqual(len(log.records), 1)
            self.assertEqual(log.records[0].levelname, 'DEBUG')
            message = log.records[0].getMessage()
            self.assertIn("Site already visited", message)
            self.assertIn("domain=example.com", message)

    def test_format_message_without_context(self):
        """Testa formatação de mensagem sem contexto"""
        logger = StructuredLogger("test_logger")
        result = logger._format_message("Simple message", {})

        self.assertEqual(result, "Simple message")

    def test_format_message_with_single_context(self):
        """Testa formatação de mensagem com contexto único"""
        logger = StructuredLogger("test_logger")
        result = logger._format_message("Message", {"key": "value"})

        self.assertEqual(result, "Message | key=value")

    def test_format_message_with_multiple_context(self):
        """Testa formatação de mensagem com múltiplo contexto"""
        logger = StructuredLogger("test_logger")
        context = {"term": "elevadores", "count": 10, "success": True}
        result = logger._format_message("Processing", context)

        self.assertIn("Processing |", result)
        self.assertIn("term=elevadores", result)
        self.assertIn("count=10", result)
        self.assertIn("success=True", result)

    def test_no_duplicate_handlers(self):
        """Testa que não cria handlers duplicados"""
        logger1 = StructuredLogger("same_logger")
        logger2 = StructuredLogger("same_logger")

        # Ambos devem referenciar o mesmo logger interno
        self.assertEqual(logger1.logger, logger2.logger)
        # Não deve duplicar handlers
        self.assertEqual(len(logger1.logger.handlers), 1)

    def test_context_with_none_values(self):
        """Testa contexto com valores None"""
        with self.assertLogs(level='INFO') as log:
            logger = StructuredLogger("test_logger")
            logger.info("Test", value=None, count=0)

            self.assertEqual(len(log.records), 1)
            message = log.records[0].getMessage()
            self.assertIn("value=None", message)
            self.assertIn("count=0", message)

    def test_context_with_special_characters(self):
        """Testa contexto com caracteres especiais"""
        with self.assertLogs(level='INFO') as log:
            logger = StructuredLogger("test_logger")
            logger.info("Test", url="https://example.com/path?param=value")

            self.assertEqual(len(log.records), 1)
            message = log.records[0].getMessage()
            self.assertIn("url=https://example.com/path?param=value", message)


if __name__ == '__main__':
    unittest.main()
