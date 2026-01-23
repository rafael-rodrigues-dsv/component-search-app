"""
Repository for TB_BAIRROS
"""
from typing import List, Dict, Any
from src.infrastructure.repositories.access_repository import AccessRepository
from pathlib import Path

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

    def list_neighborhoods(self, uf: str = None) -> List[Dict[str, Any]]:
        """Return list of neighborhoods from TB_BAIRROS ordered case-insensitive by name."""
        data_dir = Path.cwd().joinpath('data')
        data_dir.mkdir(parents=True, exist_ok=True)
        try:
            if uf:
                sql = "SELECT ID_BAIRRO AS id, NOME_BAIRRO AS nome, UF FROM TB_BAIRROS WHERE UF = ? ORDER BY UCase(NOME_BAIRRO)"
                rows = self._access.execute_query(sql, [uf])
            else:
                sql = "SELECT ID_BAIRRO AS id, NOME_BAIRRO AS nome, UF FROM TB_BAIRROS ORDER BY UCase(NOME_BAIRRO)"
                rows = self._access.execute_query(sql, None)

            if rows:
                return rows

            # fallback low-level
            conn = self._access._get_connection()
            cur = conn.cursor()
            if uf:
                cur.execute(sql, (uf,))
            else:
                cur.execute(sql)
            desc = [c[0] for c in cur.description] if cur.description else None
            fetched = cur.fetchall()
            result = []
            for r in fetched:
                if desc:
                    obj = {desc[i]: r[i] for i in range(len(desc))}
                else:
                    try:
                        obj = {'id': r[0], 'nome': r[1], 'uf': r[2]}
                    except Exception:
                        obj = {}
                result.append(obj)
            try:
                cur.close()
            except Exception:
                pass
            return result
        except Exception:
            raise
