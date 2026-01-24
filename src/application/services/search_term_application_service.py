"""
Serviço de aplicação para gerenciamento de termos de busca (integra com SearchTermRepository)
"""
from typing import List, Dict, Any
from src.infrastructure.repositories.search_term_repository import SearchTermRepository


class SearchTermApplicationService:
    def __init__(self):
        self.repo = SearchTermRepository()

    def get_active_terms(self, is_test: bool = False, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        rows = self.repo.list_active_terms(is_test=is_test)
        # Aplicar paginação simples (slice)
        if limit is None:
            return [r for r in rows]
        try:
            offset = int(offset) if offset else 0
            limit = int(limit)
            return [r for r in rows][offset:offset+limit]
        except Exception:
            return [r for r in rows]

    def propose_term(self, termo: str, is_test: bool = False, proposto_por: str = 'user') -> int:
        # Por padrão, insert como ADD
        return self.repo.insert_change(termo, 'ADD', None, proposto_por)

    def list_pending(self) -> List[Dict[str, Any]]:
        return self.repo.list_pending_changes()

    def approve(self, change_id: int, approver: str = 'admin') -> bool:
        return self.repo.approve_change(change_id, approver)

    def insert_term(self, termo: str, categoria: str = 'base', is_test: bool = False) -> int:
        return self.repo.insert_term(termo, categoria=categoria, is_test=is_test)

    def update_term_direct(self, term_id: int, new_termo: str, approver: str = 'ui') -> bool:
        # Cria change UPDATE e aprova imediatamente
        change_id = self.repo.insert_change(new_termo, 'UPDATE', term_id, proposto_por=approver)
        return self.repo.approve_change(change_id, approver=approver)

    def delete_term_direct(self, term_id: int, approver: str = 'ui') -> bool:
        change_id = self.repo.insert_change('', 'DELETE', term_id, proposto_por=approver)
        return self.repo.approve_change(change_id, approver=approver)

    def get_paginated_terms(self, limit: int, offset: int) -> Dict[str, Any]:
        """Fetch paginated terms with metadata using repository pagination where possible.
        Returns a dict with 'terms' (list of api dicts) and 'pagination' metadata.
        """
        # Parse pagination parameters strictly; let ValueError propagate
        limit = int(limit) if limit else 10
        offset = int(offset) if offset else 0

        paged = []
        total = 0
        # Try repository pagination first
        try:
            paged = self.repo.list_paginated_terms(limit=limit, offset=offset)
            total = self.repo.count_active_terms()
        except Exception:
            # Try models-based repository pagination as a second option
            models = self.repo.fetch_models_paginated(limit=limit, offset=offset)
            paged = [m.to_api_dict() for m in models]
            total = self.repo.count_active_terms() if hasattr(self.repo, 'count_active_terms') else len(paged)

        # Fallback: se não encontrou nada no banco, tentar usar as bases estáticas do settings
        if total == 0 and (not paged or len(paged) == 0):
            from config.settings import BASE_TESTES, BASE_BUSCA
            from src.infrastructure.config.config_manager import ConfigManager
            cfg = ConfigManager()
            base = BASE_TESTES if cfg.is_test_mode else BASE_BUSCA
            # transformar em dicionários compatíveis com o front
            all_terms = [{'ID_BASE': idx+1, 'TERMO_BUSCA': t, 'CATEGORIA': 'base'} for idx, t in enumerate(base)]
            paged = all_terms[offset:offset+limit]
            total = len(all_terms)

        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        current_page = (offset // limit) + 1 if limit > 0 else 1

        return {
            "terms": paged,
            "pagination": {
                "total_pages": total_pages,
                "current_page": current_page,
                "has_next": current_page < total_pages,
                "has_previous": current_page > 1
            }
        }

    def delete_base_term(self, id_base: int) -> bool:
        """Marca/exclui termo na TB_BASE_BUSCA via repositório."""
        try:
            return self.repo.delete_base_term(id_base)
        except Exception:
            return False
