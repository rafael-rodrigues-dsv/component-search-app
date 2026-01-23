from src.infrastructure.repositories.addresses_repository import AddressesRepository

class AddressesApplicationService:
    def __init__(self):
        self.repo = AddressesRepository()

    def insert_address(self, address_model):
        return self.repo.insert_address(address_model)

    def update_corrected(self, endereco_id: int, corrected_address):
        return self.repo.update_corrected(endereco_id, corrected_address)

    def fetch_with_cep_for_enrichment(self):
        return self.repo.fetch_with_cep_for_enrichment()
