from src.infrastructure.repositories.neighborhoods_repository import NeighborhoodsRepository

class NeighborhoodsApplicationService:
    def __init__(self):
        self.repo = NeighborhoodsRepository()

    def save_discovered(self, neighborhoods, uf: str):
        return self.repo.save_discovered(neighborhoods, uf)
