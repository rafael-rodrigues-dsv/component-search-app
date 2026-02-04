"""
Multi Thread Scraper Service - Com Chaveamento Inteligente
"""
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from playwright.sync_api import sync_playwright
from ..switcher.scraper_switcher import ScraperSwitcher
from ....domain.models.company_model import CompanyModel


class MultiThreadScraperService:
    """
    Service multi-thread COM chaveamento inteligente

    Cada worker usa ScraperSwitcher independentemente
    """

    def __init__(self):
        self.scraper_switcher = ScraperSwitcher()

    def collect_parallel_google(
        self,
        urls: List[str],
        max_threads: int = 5,
        max_emails: int = 5
    ) -> List[CompanyModel]:
        """
        Coleta paralela com Google

        Args:
            urls: Lista de URLs para processar
            max_threads: Máximo de threads simultâneas
            max_emails: Máximo de emails por empresa

        Returns:
            List[CompanyModel]: Empresas coletadas
        """
        results = []

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            # Submeter todas as URLs
            futures = {
                executor.submit(self._worker_google, url, max_emails): url
                for url in urls
            }

            # Coletar resultados conforme completam
            for future in as_completed(futures):
                try:
                    company = future.result(timeout=30)
                    if company and (company.emails or company.phone):
                        results.append(company)
                except Exception as e:
                    url = futures[future]
                    print(f"[ERROR] Worker Google falhou para {url}: {str(e)[:50]}")

        return results

    def collect_parallel_duckduckgo(
        self,
        urls: List[str],
        max_threads: int = 5,
        max_emails: int = 5
    ) -> List[CompanyModel]:
        """
        Coleta paralela com DuckDuckGo

        Args:
            urls: URLs para processar
            max_threads: Máximo de threads
            max_emails: Máximo de emails

        Returns:
            List[CompanyModel]: Empresas
        """
        results = []

        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            futures = {
                executor.submit(self._worker_duckduckgo, url, max_emails): url
                for url in urls
            }

            for future in as_completed(futures):
                try:
                    company = future.result(timeout=30)
                    if company and (company.emails or company.phone):
                        results.append(company)
                except Exception as e:
                    url = futures[future]
                    print(f"[ERROR] Worker DuckDuckGo falhou para {url}: {str(e)[:50]}")

        return results

    def _worker_google(self, url: str, max_emails: int) -> CompanyModel:
        """
        Worker Google com chaveamento

        Executa em thread separada

        Args:
            url: URL para processar
            max_emails: Máximo de emails

        Returns:
            CompanyModel ou None
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                try:
                    # 🆕 CHAVEAMENTO: cada worker usa switcher independentemente
                    scraper = self.scraper_switcher.get_google_scraper(page)

                    # Extração com fallback
                    company = self.scraper_switcher.extract_with_fallback(
                        scraper, url, max_emails
                    )

                    return company

                finally:
                    browser.close()

        except Exception as e:
            print(f"[ERROR] Worker Google: {str(e)[:50]}")
            return None

    def _worker_duckduckgo(self, url: str, max_emails: int) -> CompanyModel:
        """
        Worker DuckDuckGo com chaveamento

        Args:
            url: URL
            max_emails: Máximo de emails

        Returns:
            CompanyModel ou None
        """
        try:
            # Import driver manager
            try:
                from ....infrastructure.drivers.driver_manager import DriverManager
            except ImportError:
                print("[WARNING] DriverManager não encontrado")
                return None

            driver_manager = DriverManager()

            try:
                # 🆕 CHAVEAMENTO
                scraper = self.scraper_switcher.get_duckduckgo_scraper(driver_manager)

                # Extração com fallback
                company = self.scraper_switcher.extract_with_fallback(
                    scraper, url, max_emails
                )

                return company

            finally:
                driver_manager.quit()

        except Exception as e:
            print(f"[ERROR] Worker DuckDuckGo: {str(e)[:50]}")
            return None

    def collect_mixed_parallel(
        self,
        urls: List[str],
        use_google: bool = True,
        max_threads: int = 5,
        max_emails: int = 5
    ) -> List[CompanyModel]:
        """
        Coleta paralela com engine escolhida

        Args:
            urls: URLs
            use_google: True = Google, False = DuckDuckGo
            max_threads: Threads
            max_emails: Emails

        Returns:
            List[CompanyModel]
        """
        if use_google:
            return self.collect_parallel_google(urls, max_threads, max_emails)
        else:
            return self.collect_parallel_duckduckgo(urls, max_threads, max_emails)
