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
