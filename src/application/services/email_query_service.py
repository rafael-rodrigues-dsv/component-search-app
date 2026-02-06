"""
Email Query Service - Serviço de consulta de emails
Responsável por operações de leitura/query de emails (não coleta)
"""


class EmailQueryService:
    """Service para consultas de emails (read-only)"""

    def __init__(self):
        pass

    def get_paginated_emails(self, empresa_id: int = None, limit: int = 10, offset: int = 0):
        """
        Retorna emails paginados

        Args:
            empresa_id: ID da empresa (opcional)
            limit: Limite de resultados
            offset: Offset da paginação

        Returns:
            Dict com emails e metadados de paginação
        """
        try:
            from src.infrastructure.repositories.emails_repository import EmailsRepository
            repo = EmailsRepository()
            total = repo.count(empresa_id)
            models = repo.fetch_models_paginated(empresa_id=empresa_id, limit=limit, offset=offset)
            items = [m.to_api_dict() for m in models]

            try:
                limit = int(limit) if limit else 10
                offset = int(offset) if offset else 0
            except Exception:
                limit = 10
                offset = 0

            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            current_page = (offset // limit) + 1 if limit > 0 else 1

            return {
                'emails': items,
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
        except Exception:
            return {
                'emails': [],
                'pagination': {
                    'total': 0,
                    'limit': limit,
                    'offset': offset,
                    'total_pages': 1,
                    'current_page': 1,
                    'has_next': False,
                    'has_previous': False
                }
            }
