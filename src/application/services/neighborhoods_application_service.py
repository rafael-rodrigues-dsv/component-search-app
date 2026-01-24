from src.infrastructure.repositories.neighborhoods_repository import NeighborhoodsRepository
from src.domain.models.neighborhood_model import NeighborhoodModel

class NeighborhoodsApplicationService:
    def __init__(self):
        self.repo = NeighborhoodsRepository()

    def save_discovered(self, neighborhoods, uf: str):
        return self.repo.save_discovered(neighborhoods, uf)

    def get_paginated_neighborhoods(self, uf: str = None, limit: int = 10, offset: int = 0):
        # Use model-aware repository pagination
        # Parse strictly; let exceptions propagate
        limit = int(limit) if limit else 10
        offset = int(offset) if offset else 0

        total = self.repo.count(uf)
        models = self.repo.fetch_models_paginated(uf=uf, limit=limit, offset=offset)

        neighborhoods = []
        for m in models:
            try:
                if isinstance(m, NeighborhoodModel):
                    neighborhoods.append(m.to_api_dict())
                elif isinstance(m, dict):
                    neighborhoods.append({'id': m.get('id'), 'name': m.get('nome') or m.get('name'), 'uf': m.get('uf'), 'city': m.get('cidade')})
                else:
                    neighborhoods.append({'id': None, 'name': str(m), 'uf': ''})
            except Exception:
                continue

        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        current_page = (offset // limit) + 1 if limit > 0 else 1
        return {
            'neighborhoods': neighborhoods,
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
