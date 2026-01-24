"""
Repository for TB_TERMOS_BUSCA
Thin wrapper delegating to AccessRepository
"""
from typing import List, Dict, Any
from pathlib import Path
from src.infrastructure.repositories.access_repository import AccessRepository
from src.domain.models.term_model import TermModel

class TermsRepository:
    def __init__(self):
        self._repo = AccessRepository()

    def fetch_paginated(self, limit: int, offset: int) -> List[Dict[str, Any]]:
        # As Access doesn't support LIMIT/OFFSET in SQL, we fetch and slice
        all_rows = self._repo.execute_query("SELECT ID_TERMO, TERMO_COMPLETO, STATUS_PROCESSAMENTO, TIPO_LOCALIZACAO FROM TB_TERMOS_BUSCA ORDER BY ID_TERMO")
        return all_rows[offset:offset+limit]

    def fetch_models_paginated(self, limit: int, offset: int) -> List[TermModel]:
        """Retorna lista de TermModel paginada convertida a partir das linhas do DB."""
        rows = self.fetch_paginated(limit=limit, offset=offset)
        models = []
        for r in rows:
            try:
                models.append(TermModel.from_row(r))
            except Exception:
                # fallback: ignore broken rows
                continue
        return models

    def count(self) -> int:
        result = self._repo.execute_query("SELECT COUNT(*) as cnt FROM TB_TERMOS_BUSCA")
        return int(result[0].get('cnt', 0)) if result else 0

    def insert(self, termo_completo: str, tipo_localizacao: str = '', status: str = 'PENDENTE', id_base: int = None) -> int:
        params = [termo_completo, tipo_localizacao, status]
        query = "INSERT INTO TB_TERMOS_BUSCA (TERMO_COMPLETO, TIPO_LOCALIZACAO, STATUS_PROCESSAMENTO, DATA_CRIACAO) VALUES (?, ?, ?, Date())"
        # Use AccessRepository connection directly for better control
        conn = self._repo._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            cursor.execute("SELECT @@IDENTITY")
            row = cursor.fetchone()
            conn.commit()
            return row[0] if row else None
        finally:
            try:
                cursor.close()
            except Exception:
                pass

    def bulk_insert(self, terms: List[dict]) -> int:
        """Insere vários termos em batch. Espera lista de dicts {'termo':..., 'tipo_localizacao':..., 'status':...}
        Retorna número de registros inseridos."""
        if not terms:
            return 0
        conn = self._repo._get_connection()
        cursor = conn.cursor()
        try:
            data = []
            for t in terms:
                if isinstance(t, dict):
                    termo = t.get('termo') or t.get('termo_completo') or ''
                    tipo = t.get('tipo_localizacao') or t.get('tipo') or ''
                    status = t.get('status') or 'PENDENTE'
                else:
                    termo = str(t)
                    tipo = ''
                    status = 'PENDENTE'
                if termo:
                    data.append((termo, tipo, status))
            if not data:
                return 0
            cursor.executemany(
                "INSERT INTO TB_TERMOS_BUSCA (TERMO_COMPLETO, TIPO_LOCALIZACAO, STATUS_PROCESSAMENTO, DATA_CRIACAO) VALUES (?, ?, ?, Date())",
                data
            )
            conn.commit()
            return len(data)
        finally:
            try:
                cursor.close()
            except Exception:
                pass

    def delete(self, id_termo: int) -> int:
        # Verify existence first
        try:
            exists = self._repo.execute_query("SELECT ID_TERMO FROM TB_TERMOS_BUSCA WHERE ID_TERMO = ?", [id_termo])
            if not exists:
                return False
        except Exception:
            return False

        # Perform logical delete (mark as REMOVIDO) using explicit SQL via cursor to avoid potential param issues
        conn = self._repo._get_connection()
        cursor = conn.cursor()
        try:
            sql = f"UPDATE TB_TERMOS_BUSCA SET STATUS_PROCESSAMENTO = 'REMOVIDO', DATA_PROCESSAMENTO = Date() WHERE ID_TERMO = {int(id_termo)}"
            cursor.execute(sql)
            conn.commit()
            return True
        finally:
            try:
                cursor.close()
            except Exception:
                pass

    def update_status(self, id_termo: int, status: str) -> None:
        self._repo.execute_query("UPDATE TB_TERMOS_BUSCA SET STATUS_PROCESSAMENTO = ?, DATA_PROCESSAMENTO = Date() WHERE ID_TERMO = ?", [status, id_termo])

    def fetch_pending(self) -> List[Dict[str, Any]]:
        return self._repo.execute_query("SELECT ID_TERMO, TERMO_COMPLETO, TIPO_LOCALIZACAO, STATUS_PROCESSAMENTO FROM TB_TERMOS_BUSCA WHERE STATUS_PROCESSAMENTO = 'PENDENTE' ORDER BY ID_TERMO")

    def delete_all(self) -> int:
        """Remove all search terms (used by reset/clear flows)."""
        return self._repo.execute_query("DELETE FROM TB_TERMOS_BUSCA")

    def list_terms(self) -> List[Dict[str, Any]]:
        """Return all terms ordered case-insensitive by TERMO_COMPLETO."""
        # Prefer ordering in SQL using UCase for case-insensitive alphabetical order
        try:
            return self._repo.execute_query("SELECT ID_TERMO AS id, TERMO_COMPLETO AS termo_text, TIPO_LOCALIZACAO AS tipo_local, STATUS_PROCESSAMENTO AS status_proc FROM TB_TERMOS_BUSCA ORDER BY UCase(TERMO_COMPLETO)")
        except Exception:
            # Fallback to a safer query if UCase isn't supported in this environment
            return self._repo.execute_query("SELECT ID_TERMO AS id, TERMO_COMPLETO AS termo_text, TIPO_LOCALIZACAO AS tipo_local, STATUS_PROCESSAMENTO AS status_proc FROM TB_TERMOS_BUSCA ORDER BY TERMO_COMPLETO")
