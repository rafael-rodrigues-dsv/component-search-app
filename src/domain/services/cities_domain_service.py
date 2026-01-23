"""
Domain service to orchestrate cities and neighborhoods persistence and cache.
"""
from typing import List, Dict

from ...infrastructure.repositories.cities_repository import CitiesRepository
from ...infrastructure.repositories.neighborhoods_repository import NeighborhoodsRepository


class CitiesDomainService:
    def __init__(self):
        self.cities_repo = CitiesRepository()
        self.neigh_repo = NeighborhoodsRepository()

    def save_discovered(self, cities: List[Dict], neighborhoods: List[Dict], uf: str) -> Dict[str, int]:
        """Save both cities and neighborhoods. Return counts."""
        saved_cities = 0
        saved_neighborhoods = 0
        if cities:
            saved_cities = self.cities_repo.save_discovered(cities, uf)
        if neighborhoods:
            saved_neighborhoods = self.neigh_repo.save_discovered(neighborhoods, uf)
        return {'cities': saved_cities, 'neighborhoods': saved_neighborhoods}

    def create_cache_table(self):
        return self.cities_repo.create_cache_table()

    def save_cities_to_cache(self, cities: List[Dict], uf: str):
        return self.cities_repo.save_to_cache(cities, uf)

    def get_cities_from_cache(self, uf: str):
        return self.cities_repo.from_cache(uf)
