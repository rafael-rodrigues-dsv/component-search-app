from src.infrastructure.repositories.cities_repository import CitiesRepository

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
        """Return paginated cities from TB_CIDADES (database). Do NOT fallback to cache in this context.

        Raises any exception coming from repository so the caller/API can decide how to handle it.
        """
        # Consultar diretamente a tabela TB_CIDADES via repositório.
        # Qualquer exceção deve ser propagada — não usar cache como fallback aqui.
        all_cities = self.repo.list_cities(uf)

        try:
            limit = int(limit) if limit else 10
            offset = int(offset) if offset else 0
        except Exception:
            limit = 10
            offset = 0

        total = len(all_cities)
        if limit <= 0:
            paged = all_cities
        else:
            paged = all_cities[offset: offset + limit]

        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        current_page = (offset // limit) + 1 if limit > 0 else 1

        return {
            'cities': paged,
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
