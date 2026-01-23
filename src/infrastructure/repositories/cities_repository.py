"""
Repository for TB_CIDADES
Handles persistence of discovered cities into Access DB and delegates cache operations to CitiesCacheService
"""
from typing import List, Dict, Any
from src.infrastructure.repositories.access_repository import AccessRepository
from pathlib import Path

class CitiesRepository:
    def __init__(self):
        self._access = AccessRepository()

    def save_discovered(self, cities: List[Dict[str, Any]], uf: str) -> int:
        """Insert discovered cities into TB_CIDADES. Returns number inserted."""
        if not cities:
            return 0
        conn = self._access._get_connection()
        cursor = conn.cursor()
        inserted = 0
        try:
            for c in cities:
                nome = c.get('nome') or c.get('name') or c.get('nome_cidade') or c.get('municipio')
                if not nome:
                    continue
                # Avoid duplicates: case-insensitive check
                try:
                    cursor.execute("SELECT ID_CIDADE FROM TB_CIDADES WHERE UCase(NOME_CIDADE) = UCase(?) AND UF = ?", (nome, uf))
                    exists = cursor.fetchone()
                    if exists:
                        continue
                except Exception:
                    # If check fails, continue with insert attempt
                    pass

                try:
                    cursor.execute("INSERT INTO TB_CIDADES (NOME_CIDADE, UF, ATIVO, DATA_CRIACAO) VALUES (?, ?, -1, Date())", (nome, uf))
                    inserted += 1
                except Exception:
                    # ignore single-row insert errors and continue
                    continue

            conn.commit()
        finally:
            try:
                cursor.close()
            except Exception:
                pass
        return inserted

    # --- Cache related helpers delegate to CitiesCacheService (keeps single responsibility) ---
    def save_to_cache(self, cities: List[Dict], uf: str):
        try:
            from src.infrastructure.services.cities_cache_service import CitiesCacheService
            cache = CitiesCacheService()
            return cache._save_cities_to_sqlite(cities, uf)
        except Exception:
            raise

    def create_cache_table(self) -> None:
        try:
            from src.infrastructure.services.cities_cache_service import CitiesCacheService
            cache = CitiesCacheService()
            return cache._ensure_cache_db()
        except Exception:
            raise

    def from_cache(self, uf: str):
        try:
            from src.infrastructure.services.cities_cache_service import CitiesCacheService
            cache = CitiesCacheService()
            return cache._get_cities_from_cache(uf)
        except Exception:
            raise

    # New: fetch directly from TB_CIDADES (database table) - returns list of dicts with keys 'id','nome','uf'
    def list_cities(self, uf: str = None) -> List[Dict[str, Any]]:
        # Debug: append entry to data/cities_debug.log for troubleshooting
        try:
            data_dir = Path.cwd().joinpath('data')
            data_dir.mkdir(parents=True, exist_ok=True)
            try:
                with open(data_dir.joinpath('cities_debug.log'), 'a', encoding='utf-8') as dbg:
                    dbg.write(f'list_cities called (uf={uf})\n')
            except Exception:
                pass
        except Exception:
            pass

        try:
            if uf:
                sql = "SELECT ID_CIDADE AS id, NOME_CIDADE AS nome, UF FROM TB_CIDADES WHERE UF = ? ORDER BY NOME_CIDADE"
                rows = self._access.execute_query(sql, [uf])
            else:
                sql = "SELECT ID_CIDADE AS id, NOME_CIDADE AS nome, UF FROM TB_CIDADES ORDER BY NOME_CIDADE"
                rows = self._access.execute_query(sql, None)

            # If execute_query returned usable rows (list of dicts), return them
            if rows:
                try:
                    with open(data_dir.joinpath('cities_debug.log'), 'a', encoding='utf-8') as dbg:
                        dbg.write(f'execute_query returned {len(rows)} rows\n')
                        try:
                            dbg.write(f'sample_row: {rows[0]}\n')
                        except Exception:
                            pass
                except Exception:
                    pass
                return rows

            # Fallback: attempt low-level cursor fetch to handle drivers that don't populate description
            try:
                conn = self._access._get_connection()
                cur = conn.cursor()
                if uf:
                    cur.execute(sql, (uf,))
                else:
                    cur.execute(sql)
                desc = None
                try:
                    desc = [c[0] for c in cur.description] if cur.description else None
                except Exception:
                    desc = None
                fetched = cur.fetchall()
                result = []
                for r in fetched:
                    if desc:
                        obj = {desc[i]: r[i] for i in range(len(desc))}
                    else:
                        # map positional columns to id/nome/uf as a last resort
                        try:
                            obj = {'id': r[0], 'nome': r[1], 'uf': r[2]}
                        except Exception:
                            obj = {}
                    result.append(obj)
                try:
                    cur.close()
                except Exception:
                    pass
                try:
                    with open(data_dir.joinpath('cities_debug.log'), 'a', encoding='utf-8') as dbg:
                        dbg.write(f'low-level fetch returned {len(result)} rows\n')
                except Exception:
                    pass
                return result
            except Exception as e:
                # Log and re-raise for the caller to handle (no silent fallback to cache in this context)
                try:
                    self._access.logger.exception(f"list_cities fallback low-level fetch failed: {e}")
                except Exception:
                    pass
                try:
                    with open(data_dir.joinpath('cities_debug.log'), 'a', encoding='utf-8') as dbg:
                        import traceback as _tb
                        dbg.write('low-level fetch exception:\n')
                        dbg.write(_tb.format_exc() + '\n')
                except Exception:
                    pass
                raise
        except Exception:
            # Re-raise so higher-level services / API can decide how to respond (per your instruction)
            try:
                with open(data_dir.joinpath('cities_debug.log'), 'a', encoding='utf-8') as dbg:
                    import traceback as _tb
                    dbg.write('list_cities exception at top level:\n')
                    dbg.write(_tb.format_exc() + '\n')
            except Exception:
                pass
            raise
