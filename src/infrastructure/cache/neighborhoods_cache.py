"""
Cache de Bairros por Cidade
Armazena bairros descobertos via Nominatim para evitar requisições repetidas
"""
import sqlite3
import time
from pathlib import Path
from typing import List, Optional


class NeighborhoodsCache:
    """Cache persistente de bairros por cidade"""

    def __init__(self):
        self.cache_dir = Path("data/cache")
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.db_path = self.cache_dir / "pythonsearchcache.db"
        self._conn = None
        # Tabela criada por scripts/database/create_cache_db.py na inicialização

    def _get_connection(self):
        """Retorna conexão persistente (singleton)"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
        return self._conn

    def __del__(self):
        """Fecha conexão ao destruir objeto"""
        if self._conn:
            try:
                self._conn.close()
            except:
                pass


    def get_neighborhoods(self, city: str, state: str) -> Optional[List[str]]:
        """Busca bairros no cache"""
        if not city or not state:
            return None

        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT neighborhood 
                FROM neighborhoods_cache 
                WHERE LOWER(city) = LOWER(?) 
                AND LOWER(state) = LOWER(?)
                ORDER BY neighborhood
            """, (city.strip(), state.strip()))

            rows = cursor.fetchall()

            if rows:
                return [row[0] for row in rows]

            return None

        except Exception:
            return None

    def set_neighborhoods(self, city: str, state: str, neighborhoods: List[str], source: str = 'nominatim'):
        """Armazena bairros no cache"""
        if not city or not state or not neighborhoods:
            return

        try:
            conn = self._get_connection()
            timestamp = int(time.time())

            # Limpar bairros antigos desta cidade
            conn.execute("""
                DELETE FROM neighborhoods_cache 
                WHERE LOWER(city) = LOWER(?) 
                AND LOWER(state) = LOWER(?)
            """, (city.strip(), state.strip()))

            # Inserir novos bairros
            for neighborhood in neighborhoods:
                conn.execute("""
                    INSERT OR IGNORE INTO neighborhoods_cache 
                    (city, state, neighborhood, source, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (city.strip(), state.strip(), neighborhood.strip(), source, timestamp))

            conn.commit()

        except Exception as e:
            print(f"[CACHE] Erro ao salvar bairros: {e}")

    def get_stats(self) -> dict:
        """Retorna estatísticas do cache"""
        try:
            conn = self._get_connection()

            # Total de cidades com bairros
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT city || '-' || state) as total_cities,
                       COUNT(*) as total_neighborhoods
                FROM neighborhoods_cache
            """)
            row = cursor.fetchone()

            if row:
                return {
                    'total_cities': row[0],
                    'total_neighborhoods': row[1],
                    'avg_per_city': round(row[1] / row[0], 1) if row[0] > 0 else 0
                }

        except Exception:
            pass

        return {'total_cities': 0, 'total_neighborhoods': 0, 'avg_per_city': 0}

    def clear_old_entries(self, days: int = 90):
        """Remove entradas antigas do cache (padrão: 90 dias)"""
        cutoff = int(time.time()) - (days * 86400)

        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                DELETE FROM neighborhoods_cache 
                WHERE timestamp < ?
            """, (cutoff,))
            deleted = cursor.rowcount
            conn.commit()
            return deleted
        except Exception:
            return 0
