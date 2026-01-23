from src.infrastructure.repositories.zones_repository import ZonesRepository

class ZonesApplicationService:
    def __init__(self):
        self.repo = ZonesRepository()

    def insert_zone(self, nome_zona: str, uf: str, ativo: bool = True):
        return self.repo.insert_zone(nome_zona, uf, ativo)

    def count(self):
        return self.repo.count()
