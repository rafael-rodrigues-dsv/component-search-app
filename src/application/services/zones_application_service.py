from src.infrastructure.repositories.zones_repository import ZonesRepository

class ZonesApplicationService:
    def __init__(self):
        self.repo = ZonesRepository()

    def insert_zone(self, nome_zona: str, uf: str, ativo: bool = True):
        return self.repo.insert_zone(nome_zona, uf, ativo)

    def count(self):
        return self.repo.count()

    def get_paginated_zones(self, limit: int = 10, offset: int = 0):
        try:
            total = self.repo.count()
            models = self.repo.fetch_models_paginated(limit=limit, offset=offset)
            items = [m.to_api_dict() for m in models]
            try:
                limit = int(limit) if limit else 10
                offset = int(offset) if offset else 0
            except Exception:
                limit = 10
                offset = 0
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            current_page = (offset // limit) + 1 if limit > 0 else 1
            return {'zones': items, 'pagination': {'total': total, 'limit': limit, 'offset': offset, 'total_pages': total_pages, 'current_page': current_page, 'has_next': current_page < total_pages, 'has_previous': current_page > 1}}
        except Exception:
            return {'zones': [], 'pagination': {'total': 0, 'limit': limit, 'offset': offset, 'total_pages': 1, 'current_page': 1, 'has_next': False, 'has_previous': False}}
