from src.infrastructure.repositories.neighborhoods_repository import NeighborhoodsRepository

class NeighborhoodsApplicationService:
    def __init__(self):
        self.repo = NeighborhoodsRepository()

    def save_discovered(self, neighborhoods, uf: str):
        return self.repo.save_discovered(neighborhoods, uf)

    def get_paginated_neighborhoods(self, uf: str = None, limit: int = 10, offset: int = 0):
        # Query TB_BAIRROS directly; do not fallback to cache in this context
        all_items = self.repo.list_neighborhoods(uf)
        try:
            limit = int(limit) if limit else 10
            offset = int(offset) if offset else 0
        except Exception:
            limit = 10
            offset = 0
        total = len(all_items)
        paged = all_items[offset: offset + limit] if limit > 0 else all_items
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        current_page = (offset // limit) + 1 if limit > 0 else 1
        return {
            'neighborhoods': paged,
            'pagination': {
                'total': total,
                'limit': limit,
                'offset': offset,
                'total_pages': total_pages,
                'current_page': current_page,
                'has_next': current_page < total_pages,
                'has_previous': current_page > 1
            }
        }
