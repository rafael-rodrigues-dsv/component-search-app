"""
YAML Config Loader - Carrega configuração de application.yaml
"""
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class ScraperConfig:
    """Configuração do sistema de scraping"""

    # Flag principal (controla TODOS os engines)
    use_intelligent_scraper: bool

    # Rollout e fallback
    rollout_percentage: int
    fallback_to_legacy_on_error: bool
    new_scraper_timeout_seconds: int

    # Modos especiais
    comparison_mode: bool
    verbose_logging: bool

    # Modo headless
    headless: bool
    show_browser_actions: bool

    # Budgets (opcional)
    budgets: Optional[Dict] = None
    classification_thresholds: Optional[Dict] = None


class YamlConfigLoader:
    """Carrega configuração de application.yaml"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            # Caminho padrão: src/resources/application.yaml
            base_path = Path(__file__).parent.parent.parent.parent
            self.config_path = base_path / 'resources' / 'application.yaml'
        else:
            self.config_path = Path(config_path)

        self._config = None

    def load(self) -> ScraperConfig:
        """
        Carrega configuração do YAML

        Returns:
            ScraperConfig: Configuração carregada
        """
        if self._config is not None:
            return self._config

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"[WARNING] application.yaml não encontrado em {self.config_path}, usando defaults")
            return self._get_default_config()
        except Exception as e:
            print(f"[ERROR] Erro ao carregar application.yaml: {e}, usando defaults")
            return self._get_default_config()

        scraper_config = yaml_data.get('scraper', {})

        self._config = ScraperConfig(
            use_intelligent_scraper=scraper_config.get('use_intelligent_scraper', False),
            rollout_percentage=scraper_config.get('rollout_percentage', 0),
            fallback_to_legacy_on_error=scraper_config.get('fallback_to_legacy_on_error', True),
            new_scraper_timeout_seconds=scraper_config.get('new_scraper_timeout_seconds', 10),
            comparison_mode=scraper_config.get('comparison_mode', False),
            verbose_logging=scraper_config.get('verbose_logging', True),
            headless=scraper_config.get('headless', True),
            show_browser_actions=scraper_config.get('show_browser_actions', False),
            budgets=scraper_config.get('budgets'),
            classification_thresholds=scraper_config.get('classification')
        )

        return self._config

    def reload(self) -> ScraperConfig:
        """
        Recarrega configuração (útil para hot reload)

        Returns:
            ScraperConfig: Configuração recarregada
        """
        self._config = None
        return self.load()

    def _get_default_config(self) -> ScraperConfig:
        """Retorna configuração padrão (fallback)"""
        return ScraperConfig(
            use_intelligent_scraper=False,
            rollout_percentage=0,
            fallback_to_legacy_on_error=True,
            new_scraper_timeout_seconds=10,
            comparison_mode=False,
            verbose_logging=True,
            headless=True,
            show_browser_actions=False,
            budgets=None,
            classification_thresholds=None
        )


# Singleton
_loader = None


def get_scraper_config() -> ScraperConfig:
    """
    Retorna configuração carregada do YAML (singleton)

    Returns:
        ScraperConfig: Configuração global
    """
    global _loader
    if _loader is None:
        _loader = YamlConfigLoader()
    return _loader.load()


def reload_config() -> ScraperConfig:
    """
    Força recarga da configuração

    Returns:
        ScraperConfig: Configuração recarregada
    """
    global _loader
    if _loader is None:
        _loader = YamlConfigLoader()
    return _loader.reload()
