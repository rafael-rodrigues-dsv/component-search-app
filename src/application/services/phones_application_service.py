from src.infrastructure.repositories.phones_repository import PhonesRepository

class PhonesApplicationService:
    def __init__(self):
        self.repo = PhonesRepository()

    def add_phones(self, empresa_id: int, phones: list):
        return self.repo.insert_phones(empresa_id, phones)

    def count(self):
        return self.repo.count_phones()
