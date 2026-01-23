from src.infrastructure.repositories.terms_repository import TermsRepository

class ProcessedTermsApplicationService:
    def __init__(self):
        self.repo = TermsRepository()

    def get_paginated_processed_terms(self, limit: int = 10, offset: int = 0):
        # fetch from TB_TERMOS_BUSCA
        all_rows = self.repo.list_terms()
        try:
            limit = int(limit) if limit else 10
            offset = int(offset) if offset else 0
        except Exception:
            limit = 10
            offset = 0
        total = len(all_rows)
        rows = all_rows[offset: offset + limit] if limit > 0 else all_rows
        # Normalize rows: keep TERMO_COMPLETO, TIPO_LOCALIZACAO, STATUS_PROCESSAMENTO, ID_TERMO
        normalized = []
        for r in rows:
            # r might be dict with keys uppercase or lowercase
            if isinstance(r, dict):
                lower = {k.lower(): v for k, v in r.items()}
                # accept older aliases and the new safe aliases
                termo = lower.get('termo_text') or lower.get('termo_completo') or lower.get('termo') or ''
                tipo = lower.get('tipo_local') or lower.get('tipo_localizacao') or lower.get('tipo') or ''
                status = lower.get('status_proc') or lower.get('status_processamento') or lower.get('status') or ''
                idv = lower.get('id_termo') or lower.get('id') or None
            else:
                # unexpected row shape — include as is
                termo = str(r)
                tipo = ''
                status = ''
                idv = None
            normalized.append({'id': idv, 'termo_completo': termo, 'tipo_localidade': tipo, 'status': status})

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
