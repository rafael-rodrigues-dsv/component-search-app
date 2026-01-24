"""
Repository for TB_TELEFONES - implementation moved from AccessRepository
"""
from typing import List, Dict
from src.infrastructure.repositories.access_repository import AccessRepository

class PhonesRepository:
    def __init__(self):
        self._access = AccessRepository()

    def insert_phones(self, empresa_id: int, phones: List[Dict[str, str]]):
        if not phones:
            return
        conn = self._access._get_connection()
        cursor = conn.cursor()
        phone_data = [(empresa_id, tel['original'], tel['formatted'], tel.get('ddd', ''), tel.get('tipo', 'FIXO'), -1) for tel in phones]
        cursor.executemany(
            """
            INSERT INTO TB_TELEFONES (ID_EMPRESA, TELEFONE, TELEFONE_FORMATADO,
                                      DDD, TIPO_TELEFONE, VALIDADO, DATA_COLETA)
            VALUES (?, ?, ?, ?, ?, ?, Date () )
            """,
            phone_data
        )
        conn.commit()
        try:
            cursor.close()
        except Exception:
            pass

    def count_phones(self) -> int:
        """Retorna total de telefones na base"""
        try:
            rows = self._access.execute_query("SELECT COUNT(*) as cnt FROM TB_TELEFONES")
            return int(rows[0].get('cnt', 0)) if rows else 0
        except Exception:
            return 0

    def fetch_models_paginated(self, empresa_id: int = None, limit: int = 10, offset: int = 0):
        from src.domain.models.phone_model import PhoneModel
        # Parse strictly
        limit = int(limit) if limit else 10
        offset = int(offset) if offset else 0
        sql = "SELECT ID_TELEFONE AS id_telefone, ID_EMPRESA AS id_empresa, TELEFONE AS telefone, TELEFONE_FORMATADO AS telefone_formatado, DDD, TIPO_TELEFONE AS tipo FROM TB_TELEFONES"
        params = None
        if empresa_id:
            sql += " WHERE ID_EMPRESA = ?"
            params = [empresa_id]
        sql += " ORDER BY ID_TELEFONE"
        rows = self._access.execute_query(sql, params)
        models = []
        for r in rows[offset: offset + limit]:
            try:
                models.append(PhoneModel.from_row(r))
            except Exception:
                continue
        return models
