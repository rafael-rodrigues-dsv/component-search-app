"""
Scraper Service Adapter - Ponte entre Application Services e Scraper Services
"""
from typing import List, Optional
from ...infrastructure.scrapers.services.base_search_scraper_service import BaseSearchScraperService
from ...infrastructure.scrapers.services.multi_thread_scraper_service import MultiThreadScraperService
from ...domain.models.company_model import CompanyModel


class ScraperServiceAdapter:
    """
    Adapter Pattern para integrar scrapers novos nos Application Services existentes

    Uso:
    ```python
    # Em BaseSearchApplicationService:
    from src.infrastructure.scrapers.integration.scraper_service_adapter import ScraperServiceAdapter

    adapter = ScraperServiceAdapter()
    results = adapter.search_google_single_thread(
        search_term="advocacia são paulo",
        max_results=50
    )
    ```
    """

    def __init__(self):
        self.single_thread_service = BaseSearchScraperService()
        self.multi_thread_service = MultiThreadScraperService()

    # ==========================================
    # SINGLE THREAD METHODS
    # ==========================================

    def search_google_single_thread(
        self,
        search_term: str,
        max_results: int = 50,
        max_emails: int = 5,
        blacklist_hosts: Optional[List[str]] = None
    ) -> List[CompanyModel]:
        """
        Busca Google single-thread COM chaveamento

        Args:
            search_term: Termo de busca
            max_results: Máximo de resultados
            max_emails: Máximo de emails por empresa
            blacklist_hosts: Hosts para ignorar

        Returns:
            List[CompanyModel]: Empresas encontradas
        """
        return self.single_thread_service.execute_search_with_google(
            search_term=search_term,
            max_results=max_results,
            max_emails=max_emails,
            blacklist_hosts=blacklist_hosts or []
        )

    def search_duckduckgo_single_thread(
        self,
        search_term: str,
        max_results: int = 50,
        max_emails: int = 5,
        blacklist_hosts: Optional[List[str]] = None
    ) -> List[CompanyModel]:
        """
        Busca DuckDuckGo single-thread COM chaveamento

        Args:
            search_term: Termo
            max_results: Máximo
            max_emails: Emails
            blacklist_hosts: Hosts

        Returns:
            List[CompanyModel]
        """
        return self.single_thread_service.execute_search_with_duckduckgo(
            search_term=search_term,
            max_results=max_results,
            max_emails=max_emails,
            blacklist_hosts=blacklist_hosts or []
        )

    # ==========================================
    # MULTI THREAD METHODS
    # ==========================================

    def collect_urls_parallel_google(
        self,
        urls: List[str],
        max_threads: int = 5,
        max_emails: int = 5
    ) -> List[CompanyModel]:
        """
        Coleta paralela de URLs com Google

        Args:
            urls: Lista de URLs
            max_threads: Threads simultâneas
            max_emails: Emails por empresa

        Returns:
            List[CompanyModel]
        """
        return self.multi_thread_service.collect_parallel_google(
            urls=urls,
            max_threads=max_threads,
            max_emails=max_emails
        )

    def collect_urls_parallel_duckduckgo(
        self,
        urls: List[str],
        max_threads: int = 5,
        max_emails: int = 5
    ) -> List[CompanyModel]:
        """
        Coleta paralela de URLs com DuckDuckGo

        Args:
            urls: URLs
            max_threads: Threads
            max_emails: Emails

        Returns:
            List[CompanyModel]
        """
        return self.multi_thread_service.collect_parallel_duckduckgo(
            urls=urls,
            max_threads=max_threads,
            max_emails=max_emails
        )

    def collect_urls_parallel(
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
            use_google: Google ou DuckDuckGo
            max_threads: Threads
            max_emails: Emails

        Returns:
            List[CompanyModel]
        """
        return self.multi_thread_service.collect_mixed_parallel(
            urls=urls,
            use_google=use_google,
            max_threads=max_threads,
            max_emails=max_emails
        )


# Singleton para facilitar uso
_adapter_instance = None


def get_scraper_adapter() -> ScraperServiceAdapter:
    """
    Retorna instância singleton do adapter

    Returns:
        ScraperServiceAdapter
    """
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = ScraperServiceAdapter()
    return _adapter_instance
