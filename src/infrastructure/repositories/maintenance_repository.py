"""
Repository for maintenance operations that touch multiple tables (reset, cleanup)
"""
from typing import List, Dict
from src.infrastructure.repositories.access_repository import AccessRepository

class MaintenanceRepository:
    def __init__(self):
        self._access = AccessRepository()

    def reset_collected_data(self):
        """Limpa dados coletados das tabelas apropriadas e reseta estado dos termos."""
        conn = self._access._get_connection()
        cursor = conn.cursor()
        tables = [
            "TB_CEP_ENRICHMENT",
            "TB_GEOLOCALIZACAO",
            "TB_TELEFONES",
            "TB_EMAILS",
            "TB_EMPRESAS",
            "TB_PLANILHA"
        ]
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
        cursor.execute("UPDATE TB_TERMOS_BUSCA SET STATUS_PROCESSAMENTO = 'PENDENTE', DATA_PROCESSAMENTO = NULL")
        conn.commit()
        try:
            cursor.close()
        except Exception:
            pass
