"""
Testes para delay_config
"""
from unittest.mock import Mock, patch

import pytest

from src.infrastructure.config.delay_config import get_scraper_delays


class TestDelayConfig:
    """Testes para configuração de delays"""

    @patch('src.infrastructure.config.delay_config.ConfigManager')
    def test_get_scraper_delays_google(self, mock_config_manager):
        """Testa delays para Google"""
        mock_config = Mock()
        mock_config.get.side_effect = lambda key, default: {
            "delays.google.page_load_min": 1.5,
            "delays.google.page_load_max": 2.5,
            "delays.google.scroll_min": 0.8,
            "delays.google.scroll_max": 1.2
        }.get(key, default)
        mock_config_manager.return_value = mock_config

        result = get_scraper_delays("GOOGLE")

        assert result["page_load"] == (1.5, 2.5)
        assert result["scroll"] == (0.8, 1.2)

    @patch('src.infrastructure.config.delay_config.ConfigManager')
    def test_get_scraper_delays_duckduckgo(self, mock_config_manager):
        """Testa delays para DuckDuckGo"""
        mock_config = Mock()
        mock_config.get.side_effect = lambda key, default: {
            "delays.duckduckgo.page_load_min": 0.3,
            "delays.duckduckgo.page_load_max": 0.8,
            "delays.duckduckgo.scroll_min": 0.1,
            "delays.duckduckgo.scroll_max": 0.4
        }.get(key, default)
        mock_config_manager.return_value = mock_config

        result = get_scraper_delays("DUCKDUCKGO")

        assert result["page_load"] == (0.3, 0.8)
        assert result["scroll"] == (0.1, 0.4)

    @patch('src.infrastructure.config.delay_config.ConfigManager')
    def test_get_scraper_delays_default_duckduckgo(self, mock_config_manager):
        """Testa delays padrão (DuckDuckGo)"""
        mock_config = Mock()
        mock_config.get.side_effect = lambda key, default: default
        mock_config_manager.return_value = mock_config

        result = get_scraper_delays()

        assert result["page_load"] == (0.3, 0.8)
        assert result["scroll"] == (0.1, 0.4)

    @patch('src.infrastructure.config.delay_config.ConfigManager')
    def test_get_scraper_delays_case_insensitive(self, mock_config_manager):
        """Testa que engine é case insensitive"""
        mock_config = Mock()
        mock_config.get.side_effect = lambda key, default: {
            "delays.google.page_load_min": 1.5,
            "delays.google.page_load_max": 2.5,
            "delays.google.scroll_min": 0.8,
            "delays.google.scroll_max": 1.2
        }.get(key, default)
        mock_config_manager.return_value = mock_config

        result = get_scraper_delays("google")

        assert result["page_load"] == (1.5, 2.5)
        assert result["scroll"] == (0.8, 1.2)

    @patch('src.infrastructure.config.delay_config.ConfigManager')
    def test_get_scraper_delays_unknown_engine(self, mock_config_manager):
        """Testa engine desconhecido (usa DuckDuckGo como padrão)"""
        mock_config = Mock()
        mock_config.get.side_effect = lambda key, default: default
        mock_config_manager.return_value = mock_config

        result = get_scraper_delays("UNKNOWN")

        assert result["page_load"] == (0.3, 0.8)
        assert result["scroll"] == (0.1, 0.4)

    @patch('src.infrastructure.config.delay_config.ConfigManager')
    def test_get_scraper_delays_with_fallback_values(self, mock_config_manager):
        """Testa valores de fallback quando config não encontra chaves"""
        mock_config = Mock()
        mock_config.get.side_effect = lambda key, default: default  # Sempre retorna default
        mock_config_manager.return_value = mock_config

        # Testa Google com fallbacks
        result_google = get_scraper_delays("GOOGLE")
        assert result_google["page_load"] == (1.5, 2.5)
        assert result_google["scroll"] == (0.8, 1.2)

        # Testa DuckDuckGo com fallbacks
        result_ddg = get_scraper_delays("DUCKDUCKGO")
        assert result_ddg["page_load"] == (0.3, 0.8)
        assert result_ddg["scroll"] == (0.1, 0.4)
