"""
Scraper Switcher - Chaveamento inteligente entre scraper legado e novo
"""
import random
import time
from ..switcher.yaml_config_loader import get_scraper_config
from src.domain.scrapers.utils.scraper_logger import ScraperLogger


class ScraperSwitcher:
    """
    Chaveamento inteligente entre scraper legado e novo

    Suporta:
    - Feature flags via application.yaml
    - Rollout gradual (A/B testing)
    - Fallback automático
    - Modo comparação
    """

    def __init__(self):
        self.config = get_scraper_config()
        self.logger = ScraperLogger('SWITCHER')

    def get_google_scraper(self, page):
        """
        Retorna scraper do Google baseado em feature flag

        Args:
            page: Página Playwright

        Returns:
            FastSearchGoogleScraper ou DeepSearchGoogleScraper
        """
        from src.infrastructure.scrapers.engines.google.fast_search_google_scraper import FastSearchGoogleScraper
        from src.infrastructure.scrapers.engines.google.deep_search_google_scraper import DeepSearchGoogleScraper

        # Flag principal controla TUDO
        if self.config.use_intelligent_scraper:
            # Rollout gradual
            if 0 < self.config.rollout_percentage < 100:
                roll = random.randint(1, 100)
                if roll <= self.config.rollout_percentage:
                    self.logger.log('rocket', f"🆕 Google Deep Search (rollout {roll}%/{self.config.rollout_percentage}%)")
                    return DeepSearchGoogleScraper(page)
                else:
                    self.logger.log('back', f"📦 Google Fast Search (rollout {roll}%/{self.config.rollout_percentage}%)")
                    return FastSearchGoogleScraper(page)
            else:
                self.logger.log('rocket', "🆕 Google Deep Search (sistema inteligente ON)")
                return DeepSearchGoogleScraper(page)

        # Default: legado
        self.logger.log('back', "📦 Google Fast Search (sistema inteligente OFF)")
        return FastSearchGoogleScraper(page)

    def get_duckduckgo_scraper(self, page):
        """
        Retorna scraper do DuckDuckGo baseado em feature flag

        Args:
            page: Página Playwright

        Returns:
            FastSearchDuckDuckGoScraper ou DeepSearchDuckDuckGoScraper
        """
        from src.infrastructure.scrapers.engines.duckduckgo.fast_search_duckduckgo_scraper import FastSearchDuckDuckGoScraper
        from src.infrastructure.scrapers.engines.duckduckgo.deep_search_duckduckgo_scraper import DeepSearchDuckDuckGoScraper

        # Flag principal controla TUDO
        if self.config.use_intelligent_scraper:
            # Rollout gradual
            if 0 < self.config.rollout_percentage < 100:
                roll = random.randint(1, 100)
                if roll <= self.config.rollout_percentage:
                    self.logger.log('rocket', f"🆕 DuckDuckGo Deep Search (rollout {roll}%/{self.config.rollout_percentage}%)")
                    return DeepSearchDuckDuckGoScraper(page)
                else:
                    self.logger.log('back', f"📦 DuckDuckGo Fast Search (rollout {roll}%/{self.config.rollout_percentage}%)")
                    return FastSearchDuckDuckGoScraper(page)
            else:
                self.logger.log('rocket', "🆕 DuckDuckGo Deep Search (sistema inteligente ON)")
                return DeepSearchDuckDuckGoScraper(page)

        # Default: legado
        self.logger.log('back', "📦 DuckDuckGo Fast Search (sistema inteligente OFF)")
        return FastSearchDuckDuckGoScraper(page)

    def extract_with_fallback(self, scraper, url: str, max_emails: int):
        """
        Executa extração com fallback automático

        Se novo scraper falhar ou timeout:
        - Fallback para legado automaticamente

        Args:
            scraper: Instância do scraper (V2 ou legado)
            url: URL para extrair
            max_emails: Máximo de emails

        Returns:
            CompanyModel: Dados extraídos
        """
        # Import dinâmico
        from src.infrastructure.scrapers.engines.google.deep_search_google_scraper import DeepSearchGoogleScraper
        from src.infrastructure.scrapers.engines.duckduckgo.deep_search_duckduckgo_scraper import DeepSearchDuckDuckGoScraper

        is_new_scraper = isinstance(scraper, (DeepSearchGoogleScraper, DeepSearchDuckDuckGoScraper))

        if not is_new_scraper or not self.config.fallback_to_legacy_on_error:
            # Sem fallback, executa direto
            return scraper.extract_company_data(url, max_emails)

        # Tentar novo com timeout e fallback
        try:
            self.logger.log('clock', f"Tentando novo scraper (timeout: {self.config.new_scraper_timeout_seconds}s)...")

            start = time.time()
            result = scraper.extract_company_data(url, max_emails)
            elapsed = time.time() - start

            # Verificar timeout
            if elapsed > self.config.new_scraper_timeout_seconds:
                self.logger.log('warning', f"Timeout ({elapsed:.1f}s), usando legado...")
                return self._fallback_to_legacy(scraper, url, max_emails)

            # Verificar se resultado é válido
            if result.emails or result.phone:
                self.logger.log('success', "Novo scraper bem-sucedido")
                return result
            else:
                self.logger.log('warning', "Novo scraper sem resultados, tentando legado...")
                return self._fallback_to_legacy(scraper, url, max_emails)

        except Exception as e:
            self.logger.log('warning', f"Novo scraper falhou ({str(e)[:30]}), usando legado...")
            return self._fallback_to_legacy(scraper, url, max_emails)

    def _fallback_to_legacy(self, new_scraper, url: str, max_emails: int):
        """
        Executa fallback para scraper legado

        Args:
            new_scraper: Instância do scraper V2
            url: URL
            max_emails: Máximo de emails

        Returns:
            CompanyModel
        """
        from src.infrastructure.scrapers.engines.google.deep_search_google_scraper import DeepSearchGoogleScraper
        from src.infrastructure.scrapers.engines.google.fast_search_google_scraper import FastSearchGoogleScraper
        from src.infrastructure.scrapers.engines.duckduckgo.deep_search_duckduckgo_scraper import DeepSearchDuckDuckGoScraper
        from src.infrastructure.scrapers.engines.duckduckgo.fast_search_duckduckgo_scraper import FastSearchDuckDuckGoScraper
        from src.domain.models.company_model import CompanyModel

        if isinstance(new_scraper, DeepSearchGoogleScraper):
            legacy = FastSearchGoogleScraper(new_scraper.page)
            return legacy.extract_company_data(url, max_emails)

        elif isinstance(new_scraper, DeepSearchDuckDuckGoScraper):
            legacy = FastSearchDuckDuckGoScraper(new_scraper.page)
            return legacy.extract_company_data(url, max_emails)

        # Não deveria chegar aqui
        return CompanyModel(name="", emails="", domain="", url=url, html_content="")
