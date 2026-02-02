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

        import logging
        logger = logging.getLogger(__name__)

        conn = self._access._get_connection()
        cursor = conn.cursor()
        inserted = 0

        try:
            for n in neighborhoods:
                nome = n.get('name') or n.get('nome')
                cidade = n.get('city') or n.get('cidade')
                if not nome or not cidade:
                    continue

                # Normalizar nomes (remover espaços extras)
                nome = ' '.join(nome.strip().split())
                cidade = ' '.join(cidade.strip().split())

                # Obter UF do bairro (não do CEP base) e garantir uppercase
                neighborhood_uf = (n.get('state') or n.get('uf') or uf or '').strip().upper()

                if not neighborhood_uf:
                    logger.debug(f"[GEO] ⚠️ UF vazio para {nome}/{cidade}, pulando...")
                    continue

                try:
                    cursor.execute("SELECT ID_BAIRRO FROM TB_BAIRROS WHERE UCase(NOME_BAIRRO) = UCase(?) AND UCase(UF) = UCase(?)", (nome, neighborhood_uf))
                    if cursor.fetchone():
                        continue
                except Exception:
                    pass

                try:
                    # Buscar cidade com normalização
                    city_id = None
                    try:
                        cursor.execute(
                            "SELECT ID_CIDADE FROM TB_CIDADES WHERE UCase(NOME_CIDADE) = UCase(?) AND UCase(UF) = UCase(?)",
                            (cidade, neighborhood_uf)
                        )
                        r = cursor.fetchone()
                        if r:
                            city_id = r[0]
                            logger.debug(f"[GEO] ✅ Cidade encontrada: {cidade}/{neighborhood_uf} -> ID {city_id}")
                        else:
                            logger.debug(f"[GEO] ⚠️ Cidade NÃO encontrada: {cidade}/{neighborhood_uf}")
                    except Exception as e:
                        logger.debug(f"[GEO] ❌ Erro ao buscar cidade {cidade}/{neighborhood_uf}: {e}")
                        city_id = None

                    if city_id:
                        cursor.execute(
                            "INSERT INTO TB_BAIRROS (NOME_BAIRRO, UF, ID_MUNICIPIO, ATIVO, DATA_CRIACAO) VALUES (?, ?, ?, -1, Date())",
                            (nome, neighborhood_uf, city_id)
                        )
                        logger.debug(f"[GEO] ✅ Bairro inserido: {nome} -> {cidade}/{neighborhood_uf} (ID cidade: {city_id})")
                    else:
                        cursor.execute(
                            "INSERT INTO TB_BAIRROS (NOME_BAIRRO, UF, ATIVO, DATA_CRIACAO) VALUES (?, ?, -1, Date())",
                            (nome, neighborhood_uf)
                        )
                        logger.debug(f"[GEO] ⚠️ Bairro inserido SEM cidade: {nome}/{neighborhood_uf}")
                    inserted += 1
                except Exception as e:
                    logger.debug(f"[GEO] ❌ Erro ao inserir bairro {nome}/{cidade}: {e}")
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
                sql = (
                    "SELECT b.ID_BAIRRO AS id, b.NOME_BAIRRO AS nome, b.UF AS uf, b.ID_MUNICIPIO AS id_municipio, c.NOME_CIDADE AS cidade "
                    "FROM TB_BAIRROS b LEFT JOIN TB_CIDADES c ON b.ID_MUNICIPIO = c.ID_CIDADE WHERE b.UF = ? ORDER BY UCase(b.NOME_BAIRRO)"
                )
                rows = self._access.execute_query(sql, [uf])
            else:
                sql = (
                    "SELECT b.ID_BAIRRO AS id, b.NOME_BAIRRO AS nome, b.UF AS uf, b.ID_MUNICIPIO AS id_municipio, c.NOME_CIDADE AS cidade "
                    "FROM TB_BAIRROS b LEFT JOIN TB_CIDADES c ON b.ID_MUNICIPIO = c.ID_CIDADE ORDER BY UCase(b.NOME_BAIRRO)"
                )
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

    # --- NEW: model helpers ---
    def fetch_models_paginated(self, uf: str = None, limit: int = 10, offset: int = 0):
        """Return list of NeighborhoodModel instances paginated from TB_BAIRROS"""
        from src.domain.models.neighborhood_model import NeighborhoodModel
        # Parse strictly; let exceptions propagate
        limit = int(limit) if limit else 10
        offset = int(offset) if offset else 0
        rows = self.list_neighborhoods(uf)
        models = []
        for r in rows[offset: offset + limit]:
            try:
                models.append(NeighborhoodModel.from_row(r))
            except Exception:
                continue
        return models

    def count(self, uf: str = None) -> int:
        try:
            if uf:
                rows = self._access.execute_query("SELECT COUNT(*) as cnt FROM TB_BAIRROS WHERE UF = ?", [uf])
            else:
                rows = self._access.execute_query("SELECT COUNT(*) as cnt FROM TB_BAIRROS")
            if isinstance(rows, list) and rows:
                return int(rows[0].get('cnt', 0) or 0)
            return 0
        except Exception:
            return 0
