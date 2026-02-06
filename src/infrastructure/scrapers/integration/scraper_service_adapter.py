"""
Scraper Service Adapter - OBSOLETO
Use CompanySearchRouterService diretamente.
"""
from typing import List, Optional
from src.infrastructure.scrapers.services.base_search_scraper_service import BaseSearchScraperService
from src.domain.models.company_model import CompanyModel


class ScraperServiceAdapter:
    """⚠️ OBSOLETO: Use CompanySearchRouterService"""

    def __init__(self):
        self.single_thread_service = BaseSearchScraperService()

    def search_google_single_thread(
        self,
        search_term: str,
        max_results: int = 50,
        max_emails: int = 5,
        blacklist_hosts: Optional[List[str]] = None
    ) -> List[CompanyModel]:
        """Busca Google single-thread"""
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
        """Busca DuckDuckGo single-thread"""
        return self.single_thread_service.execute_search_with_duckduckgo(
            search_term=search_term,
            max_results=max_results,
            max_emails=max_emails,
            blacklist_hosts=blacklist_hosts or []
        )

    def collect_urls_parallel_google(self, urls: List[str], max_threads: int = 5, max_emails: int = 5) -> List[CompanyModel]:
        """⚠️ OBSOLETO: Use CompanySearchRouterService com processing_mode='MULTI'"""
        raise NotImplementedError("Use CompanySearchRouterService com processing_mode='MULTI'")

    def collect_urls_parallel_duckduckgo(self, urls: List[str], max_threads: int = 5, max_emails: int = 5) -> List[CompanyModel]:
        """⚠️ OBSOLETO: Use CompanySearchRouterService com processing_mode='MULTI'"""
        raise NotImplementedError("Use CompanySearchRouterService com processing_mode='MULTI'")

    def collect_urls_parallel(self, urls: List[str], use_google: bool = True, max_threads: int = 5, max_emails: int = 5) -> List[CompanyModel]:
        """⚠️ OBSOLETO: Use CompanySearchRouterService com processing_mode='MULTI'"""
        raise NotImplementedError("Use CompanySearchRouterService com processing_mode='MULTI'")


_adapter_instance = None


def get_scraper_adapter() -> ScraperServiceAdapter:
    """Retorna instância singleton do adapter"""
    global _adapter_instance
    if _adapter_instance is None:
        _adapter_instance = ScraperServiceAdapter()
    return _adapter_instance
