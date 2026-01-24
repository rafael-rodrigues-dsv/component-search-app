"""
Repository for TB_EMAILS - implementation moved from AccessRepository
"""
from typing import List
from src.infrastructure.repositories.access_repository import AccessRepository

class EmailsRepository:
    def __init__(self):
        self._access = AccessRepository()

    def insert_emails(self, empresa_id: int, emails: List[str], domain_email: str):
        """Insere vários emails em lote"""
        if not emails:
            return
        conn = self._access._get_connection()
        cursor = conn.cursor()
        email_data = [(empresa_id, email, domain_email, -1, 'SCRAPING') for email in emails]
        cursor.executemany(
            """
            INSERT INTO TB_EMAILS (ID_EMPRESA, EMAIL, DOMINIO_EMAIL,
                                   VALIDADO, DATA_COLETA, ORIGEM_COLETA)
            VALUES (?, ?, ?, ?, Date (), ?)
            """,
            email_data
        )
        conn.commit()
        try:
            cursor.close()
        except Exception:
            pass

    def is_email_collected(self, email: str) -> bool:
        try:
            conn = self._access._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM TB_EMAILS WHERE EMAIL = ?", (email,))
            result = cursor.fetchone()
            try:
                cursor.close()
            except Exception:
                pass
            return result[0] > 0
        except Exception:
            return False

    def fetch_models_paginated(self, empresa_id: int = None, limit: int = 10, offset: int = 0):
        from src.domain.models.email_model import EmailModel
        # Parse strictly; let conversion errors propagate
        limit = int(limit) if limit else 10
        offset = int(offset) if offset else 0
        sql = "SELECT ID_EMAIL AS id, ID_EMPRESA AS id_empresa, EMAIL AS email, DOMINIO_EMAIL AS dominio_email, VALIDADO FROM TB_EMAILS"
        params = None
        if empresa_id:
            sql += " WHERE ID_EMPRESA = ?"
            params = [empresa_id]
        sql += " ORDER BY ID_EMAIL"
        rows = self._access.execute_query(sql, params)
        models = []
        for r in rows[offset: offset + limit]:
            try:
                models.append(EmailModel.from_row(r))
            except Exception:
                continue
        return models

    def count(self, empresa_id: int = None) -> int:
        try:
            if empresa_id:
                rows = self._access.execute_query("SELECT COUNT(*) as cnt FROM TB_EMAILS WHERE ID_EMPRESA = ?", [empresa_id])
            else:
                rows = self._access.execute_query("SELECT COUNT(*) as cnt FROM TB_EMAILS")
            if isinstance(rows, list) and rows:
                return int(rows[0].get('cnt', 0) or 0)
            return 0
        except Exception:
            return 0
