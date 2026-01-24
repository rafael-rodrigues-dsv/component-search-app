"""
Repository wrapper for TB_ZONAS
"""
from src.infrastructure.repositories.access_repository import AccessRepository

class ZonesRepository:
    def __init__(self):
        self._repo = AccessRepository()

    def insert_zone(self, nome_zona: str, uf: str, ativo: bool = True):
        return self._repo.execute_query("INSERT INTO TB_ZONAS (NOME_ZONA, UF, ATIVO, DATA_CRIACAO) VALUES (?, ?, ?, Date())", [nome_zona, uf, int(bool(ativo))])

    def count(self) -> int:
        rows = self._repo.execute_query("SELECT COUNT(*) as cnt FROM TB_ZONAS")
        return rows[0].get('cnt', 0) if rows else 0

    def fetch_models_paginated(self, limit: int = 10, offset: int = 0):
        from src.domain.models.zone_model import ZoneModel
        # Parse strictly
        limit = int(limit) if limit else 10
        offset = int(offset) if offset else 0
        rows = self._repo.execute_query("SELECT ID_ZONA AS id_zona, NOME_ZONA AS nome, UF FROM TB_ZONAS ORDER BY NOME_ZONA")
        models = []
        for r in rows[offset: offset + limit]:
            try:
                models.append(ZoneModel.from_row(r))
            except Exception:
                continue
        return models
