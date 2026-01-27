"""
Application service for base search terms (TB_BASE_BUSCA)
"""
from typing import List, Dict, Any
from src.infrastructure.repositories.base_search_repository import BaseSearchRepository

class BaseSearchApplicationService:
    def __init__(self):
        self.repo = BaseSearchRepository()

    def list_paginated(self, page: int, page_size: int) -> Dict[str, Any]:
        offset = (page - 1) * page_size
        items = self.repo.fetch_paginated(page_size, offset)
        total = self.repo.count()
        return {'items': items, 'total': total, 'page': page, 'page_size': page_size}

    def add_term(self, term: str, category: str = '', is_test: bool = False) -> int:
        return self.repo.insert(term, category, is_test)

    def delete_term(self, id_base: int) -> bool:
        return self.repo.delete(id_base)
