"""
Application service for TB_TERMOS_BUSCA
"""
from src.infrastructure.repositories.terms_repository import TermsRepository

class TermsApplicationService:
    def __init__(self):
        self.repo = TermsRepository()

    def list_paginated(self, page: int, page_size: int):
        offset = (page - 1) * page_size
        items = self.repo.fetch_paginated(page_size, offset)
        total = self.repo.count()
        return {'items': items, 'total': total, 'page': page, 'page_size': page_size}

    def add_term(self, termo: str, tipo_localizacao: str = ''):
        return self.repo.insert(termo, tipo_localizacao)

    def delete_term(self, id_termo: int):
        return self.repo.delete(id_termo)

    def list_pending(self):
        return self.repo.fetch_pending()
