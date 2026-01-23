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
