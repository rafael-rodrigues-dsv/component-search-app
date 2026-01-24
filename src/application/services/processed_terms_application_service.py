from src.infrastructure.repositories.terms_repository import TermsRepository
from src.domain.models.term_model import TermModel

class ProcessedTermsApplicationService:
    def __init__(self):
        self.repo = TermsRepository()

    def get_paginated_processed_terms(self, limit: int = 10, offset: int = 0):
        # Use TermsRepository paginated models for better typing
        # Parse strictly; let exceptions propagate
        limit = int(limit) if limit else 10
        offset = int(offset) if offset else 0

        total = self.repo.count()
        models = self.repo.fetch_models_paginated(limit=limit, offset=offset)
        normalized = []
        for m in models:
            try:
                if isinstance(m, TermModel):
                    normalized.append({
                        'id': m.id_termo,
                        'termo_completo': m.termo_completo,
                        'tipo_localidade': m.tipo_localizacao,
                        'status': m.status_processamento
                    })
                else:
                    # fallback if model conversion failed
                    if isinstance(m, dict):
                        lower = {k.lower(): v for k, v in m.items()}
                        termo = lower.get('termo_completo') or lower.get('termo') or ''
                        tipo = lower.get('tipo_localizacao') or lower.get('tipo') or ''
                        status = lower.get('status_processamento') or lower.get('status') or ''
                        idv = lower.get('id_termo') or lower.get('id')
                        normalized.append({'id': idv, 'termo_completo': termo, 'tipo_localidade': tipo, 'status': status})
                    else:
                        normalized.append({'id': None, 'termo_completo': str(m), 'tipo_localidade': '', 'status': ''})
            except Exception:
                # ignore broken rows
                continue

        # pagination meta
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        current_page = (offset // limit) + 1 if limit > 0 else 1
        pagination = {
            'total': total,
            'limit': limit,
            'offset': offset,
            'total_pages': total_pages,
            'current_page': current_page,
            'has_next': current_page < total_pages,
            'has_previous': current_page > 1
        }
        return {'terms': normalized, 'pagination': pagination}
