"""
Scrapers Services - Integração com Application Services
"""
from .base_search_scraper_service import BaseSearchScraperService
from .collection_executor_service import CollectionExecutorService
from .fast_search_single_thread_service import FastSearchSingleThreadService
from .deep_search_single_thread_service import DeepSearchSingleThreadService
from .fast_search_multi_thread_service import FastSearchMultiThreadService
from .deep_search_multi_thread_service import DeepSearchMultiThreadService

__all__ = [
    'BaseSearchScraperService',
    'CollectionExecutorService',
    'FastSearchSingleThreadService',
    'DeepSearchSingleThreadService',
    'FastSearchMultiThreadService',
    'DeepSearchMultiThreadService',
]


