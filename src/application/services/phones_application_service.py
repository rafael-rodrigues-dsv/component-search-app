from src.infrastructure.repositories.phones_repository import PhonesRepository
from src.domain.models.phone_model import PhoneModel

class PhonesApplicationService:
    def __init__(self):
        self.repo = PhonesRepository()

    def add_phones(self, empresa_id: int, phones: list):
        return self.repo.insert_phones(empresa_id, phones)

    def count(self):
        return self.repo.count_phones()

    def get_paginated_phones(self, empresa_id: int = None, limit: int = 10, offset: int = 0):
        try:
            total = self.repo.count() if not empresa_id else self.repo.count(empresa_id)
            models = self.repo.fetch_models_paginated(empresa_id=empresa_id, limit=limit, offset=offset)
            items = [m.to_api_dict() for m in models]
            try:
                limit = int(limit) if limit else 10
                offset = int(offset) if offset else 0
            except Exception:
                limit = 10
                offset = 0
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            current_page = (offset // limit) + 1 if limit > 0 else 1
            return {'phones': items, 'pagination': {'total': total, 'limit': limit, 'offset': offset, 'total_pages': total_pages, 'current_page': current_page, 'has_next': current_page < total_pages, 'has_previous': current_page > 1}}
        except Exception:
            return {'phones': [], 'pagination': {'total': 0, 'limit': limit, 'offset': offset, 'total_pages': 1, 'current_page': 1, 'has_next': False, 'has_previous': False}}
