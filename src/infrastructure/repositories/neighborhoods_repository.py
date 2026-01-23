"""
Repository for TB_BAIRROS
"""
from typing import List, Dict, Any
from src.infrastructure.repositories.access_repository import AccessRepository

class NeighborhoodsRepository:
    def __init__(self):
        self._access = AccessRepository()

    def save_discovered(self, neighborhoods: List[Dict[str, Any]], uf: str) -> int:
        if not neighborhoods:
            return 0
        conn = self._access._get_connection()
        cursor = conn.cursor()
        inserted = 0
        try:
            for n in neighborhoods:
                nome = n.get('name') or n.get('nome')
                cidade = n.get('city') or n.get('cidade')
                if not nome or not cidade:
                    continue
                try:
                    cursor.execute("SELECT ID_BAIRRO FROM TB_BAIRROS WHERE UCase(NOME_BAIRRO) = UCase(?) AND UF = ?", (nome, uf))
                    if cursor.fetchone():
                        continue
                except Exception:
                    pass
                try:
                    cursor.execute("INSERT INTO TB_BAIRROS (NOME_BAIRRO, UF, ATIVO, DATA_CRIACAO) VALUES (?, ?, -1, Date())", (nome, uf))
                    inserted += 1
                except Exception:
                    continue
            conn.commit()
        finally:
            try:
                cursor.close()
            except Exception:
                pass
        return inserted
