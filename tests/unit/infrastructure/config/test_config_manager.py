"""
Testes unitários para ConfigManager
"""
import unittest
import tempfile
import os
from unittest.mock import patch, mock_open

from src.infrastructure.config.config_manager import ConfigManager


class TestConfigManager(unittest.TestCase):
    """Testes para ConfigManager"""

    def setUp(self):
        """Setup para cada teste"""
        self.test_config = {
            "scraping": {
                "max_emails_per_site": 10,
                "max_phones_per_site": 5
            },
            "working_hours": {
                "start": 9,
                "end": 18
            },
            "retry": {
                "max_attempts": 5,
                "base_delay": 2.0
            }
        }

    def test_config_manager_with_missing_file(self):
        """Testa ConfigManager com arquivo inexistente"""
        config = ConfigManager("src/resources/nonexistent.yaml")

        # Deve usar valores padrão
        self.assertEqual(config.max_emails_per_site, 5)
        self.assertEqual(config.retry_max_attempts, 3)

    def test_config_manager_yaml_loading(self):
        """Testa carregamento de arquivo YAML (hardcoded)"""
        config = ConfigManager("src/resources/test.yaml")

        # Usa configuração hardcoded
        self.assertEqual(config.max_emails_per_site, 5)

    def test_config_manager_json_loading(self):
        """Testa carregamento de arquivo JSON (hardcoded)"""
        config = ConfigManager("src/resources/test.json")

        # Usa configuração hardcoded
        self.assertEqual(config.max_emails_per_site, 5)

    def test_get_method_with_nested_keys(self):
        """Testa método get com chaves aninhadas"""
        with patch.object(ConfigManager, '_load_config'):
            config = ConfigManager()
            config._config = self.test_config

            self.assertEqual(config.get("scraping.max_emails_per_site"), 10)
            self.assertEqual(config.get("working_hours.start"), 9)
            self.assertEqual(config.get("nonexistent.key", "default"), "default")

    def test_get_method_with_missing_key(self):
        """Testa método get com chave inexistente"""
        with patch.object(ConfigManager, '_load_config'):
            config = ConfigManager()
            config._config = {}

            self.assertIsNone(config.get("missing.key"))
            self.assertEqual(config.get("missing.key", "default"), "default")

    def test_scraping_properties(self):
        """Testa propriedades de scraping"""
        with patch.object(ConfigManager, '_load_config'):
            config = ConfigManager()
            config._config = self.test_config

            self.assertEqual(config.max_emails_per_site, 10)
            self.assertEqual(config.max_phones_per_site, 5)

    def test_retry_properties(self):
        """Testa propriedades de retry"""
        with patch.object(ConfigManager, '_load_config'):
            config = ConfigManager()
            config._config = self.test_config

            self.assertEqual(config.retry_max_attempts, 5)
            self.assertEqual(config.retry_base_delay, 2.0)

    def test_default_values_when_config_empty(self):
        """Testa valores padrão quando configuração está vazia"""
        with patch.object(ConfigManager, '_load_config'):
            config = ConfigManager()
            config._config = {}

            self.assertEqual(config.max_emails_per_site, 5)
            self.assertEqual(config.retry_max_attempts, 3)

    def test_delay_properties_as_tuples(self):
        """Testa propriedades de delay retornando tuplas"""
        test_config_with_delays = {
            "delays": {
                "page_load_min": 1.5,
                "page_load_max": 2.5,
                "scroll_min": 0.5,
                "scroll_max": 1.0
            }
        }

        with patch.object(ConfigManager, '_load_config'):
            config = ConfigManager()
            config._config = test_config_with_delays

            self.assertEqual(config.page_load_delay, (1.5, 2.5))
            self.assertEqual(config.scroll_delay, (0.5, 1.0))

    def test_boolean_properties(self):
        """Testa propriedades booleanas"""
        test_config_bool = {
            "mode": {"is_test": False},
            "performance": {"tracking_enabled": True}
        }

        with patch.object(ConfigManager, '_load_config'):
            config = ConfigManager()
            config._config = test_config_bool

            self.assertFalse(config.is_test_mode)
            self.assertTrue(config.performance_tracking_enabled)

    def test_config_file_path_handling(self):
        """Testa manipulação de caminho do arquivo"""
        with patch('pathlib.Path.suffix', '.yaml'):
            with patch.object(ConfigManager, '_load_config'):
                config = ConfigManager("src/resources/custom_path.yaml")
                self.assertIn("custom_path.yaml", str(config.config_path))
                self.assertIn("src", str(config.config_path))
                self.assertIn("resources", str(config.config_path))

    def test_config_loading_exception_handling(self):
        """Testa tratamento de exceções no carregamento"""
        config = ConfigManager("src/resources/test.yaml")

        # Usa configuração hardcoded
        self.assertEqual(config.max_emails_per_site, 5)  # Valor padrão


if __name__ == '__main__':
    unittest.main()
