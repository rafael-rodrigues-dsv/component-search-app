"""
Fast Search Multi-Thread Service - Sistema legado/rápido
Processamento paralelo sem classificação inteligente de sites
"""
from typing import List
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright
from ..switcher.scraper_switcher import ScraperSwitcher
from ....domain.models.company_model import CompanyModel


class FastSearchMultiThreadService:
    """
    Multi-thread service para Fast Search (legado/rápido)

    Características:
    - Processamento paralelo simples
    - Usa scrapers Fast Search
    - Sem classificação de sites
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
        Coleta paralela com Google Fast Search

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
        Coleta paralela com DuckDuckGo Fast Search

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
        Worker Google Fast Search

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
                    # Força usar Fast Search (sem chaveamento)
                    from ..engines.google.fast_search_google_scraper import FastSearchGoogleScraper
                    scraper = FastSearchGoogleScraper(page)

                    # Extração direta
                    company = scraper.extract_company_data(url, max_emails)
                    return company

                finally:
                    browser.close()

        except Exception as e:
            print(f"[ERROR] Worker Google: {str(e)[:50]}")
            return None

    def _worker_duckduckgo(self, url: str, max_emails: int) -> CompanyModel:
        """
        Worker DuckDuckGo Fast Search

        Args:
            url: URL
            max_emails: Máximo de emails

        Returns:
            CompanyModel ou None
        """
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                try:
                    # Força usar Fast Search (sem chaveamento)
                    from ..engines.duckduckgo.fast_search_duckduckgo_scraper import FastSearchDuckDuckGoScraper
                    scraper = FastSearchDuckDuckGoScraper(page)

                    # Extração direta
                    company = scraper.extract_company_data(url, max_emails)
                    return company

                finally:
                    browser.close()

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
