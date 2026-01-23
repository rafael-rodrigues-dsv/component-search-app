"""
Repository for TB_BASE_BUSCA (base search terms)
This is a thin wrapper around AccessRepository to isolate table-specific logic.
"""
from typing import List, Dict, Any
from src.infrastructure.repositories.access_repository import AccessRepository

class BaseSearchRepository:
    def __init__(self):
        self._repo = AccessRepository()

    def fetch_paginated(self, limit: int, offset: int) -> List[Dict[str, Any]]:
        query = "SELECT ID_BASE, TERMO_BUSCA, CATEGORIA, ATIVO, IS_TEST FROM TB_BASE_BUSCA ORDER BY ID_BASE"
        params = None
        # Access ODBC doesn't support LIMIT/OFFSET, pagination should be handled by callers or by query patterns.
        return self._repo.execute_query(query, params)[:limit]

    def count(self) -> int:
        return self._repo.execute_query("SELECT COUNT(*) as cnt FROM TB_BASE_BUSCA")[0].get('cnt', 0) if self._repo.execute_query("SELECT COUNT(*) as cnt FROM TB_BASE_BUSCA") else 0

    def insert(self, term: str, category: str = '', is_test: bool = False) -> int:
        # delegate to AccessRepository generic execute_query for insert
        query = "INSERT INTO TB_BASE_BUSCA (TERMO_BUSCA, CATEGORIA, ATIVO, DATA_CRIACAO, IS_TEST) VALUES (?, ?, -1, Date(), ?)"
        self._repo.execute_query(query, [term, category, int(bool(is_test))])
        # return approximate identity using SELECT @@IDENTITY
        result = self._repo.fetch_one("SELECT @@IDENTITY")
        return result[0] if result else None

    def delete(self, id_base: int) -> int:
        return self._repo.execute_query("DELETE FROM TB_BASE_BUSCA WHERE ID_BASE = ?", [id_base])
