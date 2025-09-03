"""
Gerenciador de configurações via YAML/JSON
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Union


class ConfigManager:
    """Gerenciador centralizado de configurações"""

    def __init__(self, config_path: str = "src/resources/application.yaml"):
        self.config_path = self._validate_path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _validate_path(self, path: str) -> Path:
        """Valida e sanitiza o caminho do arquivo para prevenir path traversal"""
        # Resolve o caminho absoluto
        resolved_path = Path(path).resolve()

        # Define diretório base permitido (raiz do projeto)
        base_dir = Path.cwd().resolve()

        # Verifica se o caminho está dentro do diretório permitido
        try:
            resolved_path.relative_to(base_dir)
        except ValueError:
            raise ValueError(f"Caminho não permitido: {path}. Deve estar dentro de {base_dir}")

        return resolved_path

    def _load_config(self) -> None:
        """Carrega configuração do arquivo"""
        # Configuração padrão hardcoded
        self._config = {
            'scraping': {
                'max_emails_per_site': 5,
                'max_phones_per_site': 3,
                'results_per_term_limit': 1200
            },

            'retry': {
                'max_attempts': 3,
                'base_delay': 1.0,
                'backoff_factor': 2.0,
                'max_delay': 60.0
            },
            'delays': {
                'page_load_min': 2.0,
                'page_load_max': 3.0,
                'scroll_min': 1.0,
                'scroll_max': 1.5,
                'search_dwell_min': 1.2,
                'search_dwell_max': 2.4
            },
            'mode': {
                'is_test': True,
                'complete_threshold': 1000
            },
            'performance': {
                'tracking_enabled': True
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Obtém valor por chave aninhada (ex: 'scraping.max_emails_per_site')"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    # Propriedades de scraping
    @property
    def max_emails_per_site(self) -> int:
        return self.get('scraping.max_emails_per_site', 5)

    @property
    def max_phones_per_site(self) -> int:
        return self.get('scraping.max_phones_per_site', 3)

    @property
    def results_per_term_limit(self) -> int:
        return self.get('scraping.results_per_term_limit', 1200)

    # Propriedades de retry
    @property
    def retry_max_attempts(self) -> int:
        return self.get('retry.max_attempts', 3)

    @property
    def retry_base_delay(self) -> float:
        return self.get('retry.base_delay', 1.0)

    @property
    def retry_backoff_factor(self) -> float:
        return self.get('retry.backoff_factor', 2.0)

    @property
    def retry_max_delay(self) -> float:
        return self.get('retry.max_delay', 60.0)

    # Propriedades de delays
    @property
    def page_load_delay(self) -> tuple:
        min_delay = self.get('delays.page_load_min', 2.0)
        max_delay = self.get('delays.page_load_max', 3.0)
        return (min_delay, max_delay)

    @property
    def scroll_delay(self) -> tuple:
        min_delay = self.get('delays.scroll_min', 1.0)
        max_delay = self.get('delays.scroll_max', 1.5)
        return (min_delay, max_delay)

    @property
    def search_dwell_delay(self) -> tuple:
        min_delay = self.get('delays.search_dwell_min', 1.2)
        max_delay = self.get('delays.search_dwell_max', 2.4)
        return (min_delay, max_delay)

    # Propriedades de modo
    @property
    def is_test_mode(self) -> bool:
        return self.get('mode.is_test', True)

    @property
    def complete_mode_threshold(self) -> int:
        return self.get('mode.complete_threshold', 1000)

    # Propriedades de performance
    @property
    def performance_tracking_enabled(self) -> bool:
        return self.get('performance.tracking_enabled', True)
