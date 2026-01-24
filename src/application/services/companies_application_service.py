from src.infrastructure.repositories.companies_repository import CompaniesRepository
from src.domain.models.company_model import CompanyModel

class CompaniesApplicationService:
    def __init__(self):
        self.repo = CompaniesRepository()

    def insert_company(self, *args, **kwargs):
        return self.repo.insert_company(*args, **kwargs)

    def update_status(self, empresa_id: int, status: str, nome_empresa: str = None):
        return self.repo.update_status(empresa_id, status, nome_empresa)

    def is_domain_visited(self, domain: str):
        return self.repo.is_domain_visited(domain)

    def get_paginated_companies_for_term(self, id_termo: int = None, limit: int = 10, offset: int = 0):
        # Parse pagination parameters strictly; let exceptions propagate to caller if invalid
        limit = int(limit) if limit else 10
        offset = int(offset) if offset else 0

        total = self.repo.count(id_termo)
        models = self.repo.fetch_models_paginated(id_termo, limit=limit, offset=offset)
        result = []
        for m in models:
            try:
                if isinstance(m, CompanyModel):
                    result.append(m.to_api_dict())
                elif isinstance(m, dict):
                    result.append({ 'id': m.get('id'), 'site_url': m.get('site_url'), 'domain': m.get('dominio'), 'status': m.get('status') })
                else:
                    result.append({'id': None, 'site_url': str(m)})
            except Exception:
                continue

        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        current_page = (offset // limit) + 1 if limit > 0 else 1
        return {'companies': result, 'pagination': {'total': total, 'limit': limit, 'offset': offset, 'total_pages': total_pages, 'current_page': current_page, 'has_next': current_page < total_pages, 'has_previous': current_page > 1}}
