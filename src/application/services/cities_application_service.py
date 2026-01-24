from src.infrastructure.repositories.cities_repository import CitiesRepository
from src.domain.models.city_model import CityModel

class CitiesApplicationService:
    def __init__(self):
        self.repo = CitiesRepository()

    def save_discovered(self, cities, uf: str) -> int:
        return self.repo.save_discovered(cities, uf)

    def save_to_cache(self, cities, uf: str):
        return self.repo.save_to_cache(cities, uf)

    def create_cache_table(self):
        return self.repo.create_cache_table()

    def from_cache(self, uf: str):
        return self.repo.from_cache(uf)

    def get_paginated_cities(self, uf: str, limit: int = 10, offset: int = 0):
        """Return paginated cities from TB_CIDADES (database) using CityModel objects.

        Raises any exception coming from repository so the caller/API can decide how to handle it.
        """
        # Parse strictly; let ValueError propagate
        limit = int(limit) if limit else 10
        offset = int(offset) if offset else 0

        total = self.repo.count(uf)
        models = self.repo.fetch_models_paginated(uf=uf, limit=limit, offset=offset)

        cities = []
        for m in models:
            try:
                if isinstance(m, CityModel):
                    cities.append(m.to_api_dict())
                elif isinstance(m, dict):
                    # fallback
                    cities.append({'id': m.get('id'), 'name': m.get('nome') or m.get('name'), 'uf': m.get('uf')})
                else:
                    cities.append({'id': None, 'name': str(m), 'uf': ''})
            except Exception:
                continue

        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        current_page = (offset // limit) + 1 if limit > 0 else 1

        return {
            'cities': cities,
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
