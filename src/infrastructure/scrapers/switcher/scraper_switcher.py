"""
Scraper Switcher - Chaveamento inteligente entre scraper legado e novo
"""
import random
import time
from typing import Union, Optional
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
            GoogleScraperPlaywright ou GoogleScraperV2
        """
        from src.infrastructure.scrapers.google_scraper_playwright import GoogleScraperPlaywright
        from src.infrastructure.scrapers.engines.google.google_scraper_v2 import GoogleScraperV2

        # Flag principal controla TUDO
        if self.config.use_intelligent_scraper:
            # Rollout gradual
            if 0 < self.config.rollout_percentage < 100:
                roll = random.randint(1, 100)
                if roll <= self.config.rollout_percentage:
                    self.logger.log('rocket', f"🆕 Google Scraper V2 (rollout {roll}%/{self.config.rollout_percentage}%)")
                    return GoogleScraperV2(page)
                else:
                    self.logger.log('back', f"📦 Google Scraper Legacy (rollout {roll}%/{self.config.rollout_percentage}%)")
                    return GoogleScraperPlaywright(page)
            else:
                self.logger.log('rocket', "🆕 Google Scraper V2 (sistema inteligente ON)")
                return GoogleScraperV2(page)

        # Default: legado
        self.logger.log('back', "📦 Google Scraper Legacy (sistema inteligente OFF)")
        return GoogleScraperPlaywright(page)

    def get_duckduckgo_scraper(self, driver_manager):
        """
        Retorna scraper do DuckDuckGo baseado em feature flag

        Args:
            driver_manager: Driver manager

        Returns:
            DuckDuckGoScraperPlaywright ou DuckDuckGoScraperV2
        """
        from src.infrastructure.scrapers.duckduckgo_scraper_playwright import DuckDuckGoScraperPlaywright
        from src.infrastructure.scrapers.engines.duckduckgo.duckduckgo_scraper_v2 import DuckDuckGoScraperV2

        # Flag principal controla TUDO
        if self.config.use_intelligent_scraper:
            # Rollout gradual
            if 0 < self.config.rollout_percentage < 100:
                roll = random.randint(1, 100)
                if roll <= self.config.rollout_percentage:
                    self.logger.log('rocket', f"🆕 DuckDuckGo Scraper V2 (rollout {roll}%/{self.config.rollout_percentage}%)")
                    return DuckDuckGoScraperV2(driver_manager)
                else:
                    self.logger.log('back', f"📦 DuckDuckGo Scraper Legacy (rollout {roll}%/{self.config.rollout_percentage}%)")
                    return DuckDuckGoScraperPlaywright(driver_manager)
            else:
                self.logger.log('rocket', "🆕 DuckDuckGo Scraper V2 (sistema inteligente ON)")
                return DuckDuckGoScraperV2(driver_manager)

        # Default: legado
        self.logger.log('back', "📦 DuckDuckGo Scraper Legacy (sistema inteligente OFF)")
        return DuckDuckGoScraperPlaywright(driver_manager)

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
        from src.infrastructure.scrapers.engines.google.google_scraper_v2 import GoogleScraperV2
        from src.infrastructure.scrapers.engines.duckduckgo.duckduckgo_scraper_v2 import DuckDuckGoScraperV2

        is_new_scraper = isinstance(scraper, (GoogleScraperV2, DuckDuckGoScraperV2))

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
        from src.infrastructure.scrapers.engines.google.google_scraper_v2 import GoogleScraperV2
        from src.infrastructure.scrapers.google_scraper_playwright import GoogleScraperPlaywright
        from src.infrastructure.scrapers.engines.duckduckgo.duckduckgo_scraper_v2 import DuckDuckGoScraperV2
        from src.infrastructure.scrapers.duckduckgo_scraper_playwright import DuckDuckGoScraperPlaywright
        from src.domain.models.company_model import CompanyModel

        if isinstance(new_scraper, GoogleScraperV2):
            legacy = GoogleScraperPlaywright(new_scraper.page)
            return legacy.extract_company_data(url, max_emails)

        elif isinstance(new_scraper, DuckDuckGoScraperV2):
            legacy = DuckDuckGoScraperPlaywright(new_scraper.driver_manager)
            return legacy.extract_company_data(url, max_emails)

        # Não deveria chegar aqui
        return CompanyModel(name="", emails="", domain="", url=url, html_content="")
