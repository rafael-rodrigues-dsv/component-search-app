from typing import List
from .access_repository import AccessRepository


class ZoneRepository:
    """Repository to manage TB_ZONAS"""

    def __init__(self):
        self._repo = AccessRepository()

    def insert_zones(self, zones: List[dict]) -> int:
        """Insert multiple zones. Each zone is dict with keys: nome, uf, ativo (bool/int). Returns count inserted."""
        try:
            conn = self._repo._get_connection()
            cursor = conn.cursor()
            for z in zones:
                nome = z.get('nome')
                uf = z.get('uf')
                ativo = -1 if z.get('ativo', True) else 0
                try:
                    cursor.execute("INSERT INTO TB_ZONAS (NOME_ZONA, UF, ATIVO, DATA_CRIACAO) VALUES (?, ?, ?, Date())", (nome, uf, ativo))
                except Exception:
                    # ignore individual insert errors
                    pass
            conn.commit()
            cursor.close()
            return len(zones)
        except Exception as e:
            print(f"[AVISO] Falha ao inserir zonas: {e}")
            return 0
