"""
Base Search Service - Single Thread com Chaveamento Inteligente
"""
from typing import List
from playwright.sync_api import sync_playwright
from ..switcher.scraper_switcher import ScraperSwitcher
from ....domain.models.company_model import CompanyModel


class BaseSearchScraperService:
    """
    Service para buscas single-thread COM chaveamento inteligente

    Integra ScraperSwitcher para alternar entre legado e novo
    """

    def __init__(self):
        self.scraper_switcher = ScraperSwitcher()

    def execute_search_with_google(
        self,
        search_term: str,
        max_results: int = 50,
        max_emails: int = 5,
        blacklist_hosts: List[str] = None
    ) -> List[CompanyModel]:
        """
        Busca com Google (COM CHAVEAMENTO)

        Args:
            search_term: Termo de busca
            max_results: Máximo de resultados
            max_emails: Máximo de emails por empresa
            blacklist_hosts: Hosts para ignorar

        Returns:
            List[CompanyModel]: Empresas encontradas
        """
        blacklist_hosts = blacklist_hosts or []
        results = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                # 🆕 CHAVEAMENTO: pega scraper baseado em application.yaml
                scraper = self.scraper_switcher.get_google_scraper(page)

                # Executa busca (interface compatível)
                if scraper.search(search_term):
                    links = scraper.get_result_links(blacklist_hosts)

                    # Processar links
                    for url in links[:max_results]:
                        # 🆕 CHAVEAMENTO: extração com fallback automático
                        company = self.scraper_switcher.extract_with_fallback(
                            scraper, url, max_emails
                        )

                        # Validar dados
                        if company.emails or company.phone:
                            results.append(company)

                        # Early exit se atingiu limite
                        if len(results) >= max_results:
                            break

            finally:
                browser.close()

        return results

    def execute_search_with_duckduckgo(
        self,
        search_term: str,
        max_results: int = 50,
        max_emails: int = 5,
        blacklist_hosts: List[str] = None
    ) -> List[CompanyModel]:
        """
        Busca com DuckDuckGo (COM CHAVEAMENTO)

        Args:
            search_term: Termo de busca
            max_results: Máximo de resultados
            max_emails: Máximo de emails
            blacklist_hosts: Hosts para ignorar

        Returns:
            List[CompanyModel]: Empresas encontradas
        """
        blacklist_hosts = blacklist_hosts or []
        results = []

        # Import driver manager (assumindo que existe)
        try:
            from ....infrastructure.drivers.driver_manager import DriverManager
        except ImportError:
            # Fallback se não existir
            print("[WARNING] DriverManager não encontrado, pulando DuckDuckGo")
            return results

        driver_manager = DriverManager()

        try:
            # 🆕 CHAVEAMENTO: pega scraper baseado em application.yaml
            scraper = self.scraper_switcher.get_duckduckgo_scraper(driver_manager)

            if scraper.search(search_term):
                links = scraper.get_result_links(blacklist_hosts)

                for url in links[:max_results]:
                    # 🆕 CHAVEAMENTO: extração com fallback
                    company = self.scraper_switcher.extract_with_fallback(
                        scraper, url, max_emails
                    )

                    if company.emails or company.phone:
                        results.append(company)

                    if len(results) >= max_results:
                        break

        finally:
            driver_manager.quit()

        return results
