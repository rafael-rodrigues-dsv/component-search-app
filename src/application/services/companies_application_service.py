from src.infrastructure.repositories.companies_repository import CompaniesRepository

class CompaniesApplicationService:
    def __init__(self):
        self.repo = CompaniesRepository()

    def insert_company(self, *args, **kwargs):
        return self.repo.insert_company(*args, **kwargs)

    def update_status(self, empresa_id: int, status: str, nome_empresa: str = None):
        return self.repo.update_status(empresa_id, status, nome_empresa)

    def is_domain_visited(self, domain: str):
        return self.repo.is_domain_visited(domain)
