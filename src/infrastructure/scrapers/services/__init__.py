"""
Scrapers Services - Integração com Application Services
"""
from .base_search_scraper_service import BaseSearchScraperService
from .multi_thread_scraper_service import MultiThreadScraperService

__all__ = [
    'BaseSearchScraperService',
    'MultiThreadScraperService',
]
