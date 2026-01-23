"""
Gerenciador de configurações via YAML/JSON
"""
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    """Gerenciador centralizado de configurações

    Observação: a propriedade `reference_cep` NÃO utiliza cache e consulta a
    tabela `TB_CEP_CONFIG` via `ZipCodeApplicationService` a cada acesso.
    """

    def __init__(self, config_path: str = "src/resources/application.yaml"):
        self.config_path = self._validate_path(config_path)
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _validate_path(self, path: str) -> Path:
        """Valida e sanitiza o caminho do arquivo para prevenir path traversal"""
        resolved_path = Path(path).resolve()
        base_dir = Path.cwd().resolve()
        try:
            resolved_path.relative_to(base_dir)
        except ValueError:
            raise ValueError(f"Caminho não permitido: {path}. Deve estar dentro de {base_dir}")
        return resolved_path

    def _load_config(self) -> None:
        """Carrega configuração do arquivo YAML"""
        default_config = {
            'search': {
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
                    'duckduckgo': {
                        'page_load_min': 2.0,
                        'page_load_max': 3.0,
                        'scroll_min': 1.0,
                        'scroll_max': 1.5,
                        'search_dwell_min': 1.2,
                        'search_dwell_max': 2.4
                    }
                }
            },
            'mode': {
                'is_test': False,
                'complete_threshold': 1000
            },
            'performance': {
                'tracking_enabled': True
            }
        }

        try:
            if self.config_path.exists():
                import yaml
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        self._config = file_config
                        return
        except Exception as e:
            print(f"Erro ao carregar YAML: {e}")

        self._config = default_config

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    # ---------- properties ----------
    @property
    def reference_cep(self) -> str:
        """Retorna o CEP de referência lendo diretamente TB_CEP_CONFIG via service.

        Levanta ValueError se não houver valor na tabela e não houver CEP no YAML.
        """
        try:
            from src.application.services.zip_code_application_service import ZipCodeApplicationService
            svc = ZipCodeApplicationService()
            row = svc.get_reference_cep()
            if not row or not isinstance(row, dict) or not row.get('cep'):
                raise ValueError('CEP de referência não encontrado no banco (TB_CEP_CONFIG)')
            return row.get('cep')
        except Exception:
            # Propagar erro para que chamador trate
            raise

    def _validate_capital_cep(self, cep: str) -> dict:
        try:
            from ..services.capital_cep_validator import CapitalCepValidator
            validator = CapitalCepValidator()
            return validator.validate_capital_cep(cep)
        except Exception as e:
            return {
                'valid': False,
                'error': f'Erro na validação: {e}'
            }

    # Propriedades de scraping
    @property
    def max_emails_per_site(self) -> int:
        return self.get('search.scraping.max_emails_per_site', 5)

    @property
    def max_phones_per_site(self) -> int:
        return self.get('search.scraping.max_phones_per_site', 3)

    @property
    def results_per_term_limit(self) -> int:
        return self.get('search.scraping.results_per_term_limit', 1200)

    # Propriedades de retry
    @property
    def retry_max_attempts(self) -> int:
        return self.get('search.retry.max_attempts', 3)

    @property
    def retry_base_delay(self) -> float:
        return self.get('search.retry.base_delay', 1.0)

    @property
    def retry_backoff_factor(self) -> float:
        return self.get('search.retry.backoff_factor', 2.0)

    @property
    def retry_max_delay(self) -> float:
        return self.get('search.retry.max_delay', 60.0)

    # Propriedades de delays (agora em search.delays)
    @property
    def page_load_delay(self) -> tuple:
        min_delay = self.get('search.delays.duckduckgo.page_load_min', 2.0)
        max_delay = self.get('search.delays.duckduckgo.page_load_max', 3.0)
        return (min_delay, max_delay)

    @property
    def scroll_delay(self) -> tuple:
        min_delay = self.get('search.delays.duckduckgo.scroll_min', 1.0)
        max_delay = self.get('search.delays.duckduckgo.scroll_max', 1.5)
        return (min_delay, max_delay)

    @property
    def search_dwell_delay(self) -> tuple:
        min_delay = self.get('search.delays.duckduckgo.search_dwell_min', 1.2)
        max_delay = self.get('search.delays.duckduckgo.search_dwell_max', 2.4)
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

    # Propriedades de geolocalização
    @property
    def geographic_discovery_enabled(self) -> bool:
        return self.get('geographic_discovery.enabled', True)
    
    @property
    def cep_enrichment_widget_enabled(self) -> bool:
        return self.get('ui.widgets.cep_enrichment.enabled', True)

    @property
    def geolocation_widget_enabled(self) -> bool:
        return self.get('ui.widgets.geolocation.enabled', True)

    @property
    def capital_validation_enabled(self) -> bool:
        return self.get('geographic_discovery.capital_validation.enabled', True)
    
    def get_capital_info(self) -> dict:
        try:
            from ..services.capital_cep_validator import CapitalCepValidator
            validator = CapitalCepValidator()
            return validator.validate_capital_cep(self.reference_cep)
        except Exception:
            return {'valid': False, 'error': 'Erro ao obter informações da capital'}

    def get_config_value(self, key: str, default: Any = None) -> Any:
        return self.get(key, default)
