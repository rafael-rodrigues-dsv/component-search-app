"""
Cache de Bairros por Cidade
Usa dados do GeoNames (100% offline após carga inicial)
"""
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Tuple
import logging


class NeighborhoodsCache:
    """Cache persistente de bairros por cidade usando GeoNames"""

    def __init__(self):
        self.cache_dir = Path("data/cache")
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.db_path = self.cache_dir / "pythonsearchcache.db"
        self._conn = None
        self.logger = logging.getLogger(__name__)
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

    def is_geonames_loaded(self) -> bool:
        """Verifica se dados GeoNames estão carregados"""
        try:
            conn = self._get_connection()

            # Verificar se a tabela existe primeiro
            cursor = conn.execute("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='table' AND name='neighborhoods_geonames'
            """)
            table_exists = cursor.fetchone()[0] > 0

            if not table_exists:
                return False

            # Agora sim, verificar se tem dados
            cursor = conn.execute("SELECT COUNT(*) FROM neighborhoods_geonames")
            count = cursor.fetchone()[0]
            return count > 0
        except Exception:
            return False

    def get_neighborhoods_from_geonames(self, city: str, state: str, limit: int = 50) -> List[Dict[str, any]]:
        """
        Busca bairros diretamente do GeoNames (100% offline)
        Retorna lista de dicionários com name, latitude, longitude
        """
        if not city or not state:
            return []

        try:
            conn = self._get_connection()

            # Buscar bairros no GeoNames
            cursor = conn.execute("""
                SELECT DISTINCT name, latitude, longitude, feature_code, population
                FROM neighborhoods_geonames
                WHERE state_code = ?
                AND (
                    UPPER(name) LIKE '%' || UPPER(?) || '%'
                    OR admin2_code IN (
                        SELECT ibge_code FROM cities_ibge 
                        WHERE UPPER(name) = UPPER(?) AND state_code = ?
                    )
                )
                ORDER BY 
                    CASE 
                        WHEN feature_code = 'PPLX' THEN 1
                        WHEN feature_code = 'PPL' THEN 2
                        ELSE 3
                    END,
                    population DESC,
                    name
                LIMIT ?
            """, (state, city, city, state, limit))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'name': row[0],
                    'latitude': row[1],
                    'longitude': row[2],
                    'feature_code': row[3],
                    'population': row[4]
                })

            return results

        except Exception as e:
            self.logger.error(f"[GEONAMES] ❌ Erro ao buscar bairros de {city}/{state}: {e}")
            return []

    def get_neighborhoods(self, city: str, state: str) -> Optional[List[str]]:
        """Busca bairros no cache (compatibilidade com código antigo)"""
        neighborhoods = self.get_neighborhoods_from_geonames(city, state)
        if neighborhoods:
            return [n['name'] for n in neighborhoods]
        return None

    def get_city_coordinates(self, city: str, state: str) -> Optional[Tuple[float, float]]:
        """
        Retorna coordenadas (lat, lon) de uma cidade do cache
        Busca em: municipalities_coordinates → cities_ibge → neighborhoods_geonames
        """
        if not city or not state:
            return None

        try:
            conn = self._get_connection()

            # 1. Tentar municipalities_coordinates (mais rápido)
            cursor = conn.execute("""
                SELECT latitude, longitude 
                FROM municipalities_coordinates
                WHERE UPPER(city) = UPPER(?) AND UPPER(state) = UPPER(?)
                LIMIT 1
            """, (city, state))

            result = cursor.fetchone()
            if result and result[0] and result[1]:
                return (result[0], result[1])

            # 2. Tentar cities_ibge
            cursor = conn.execute("""
                SELECT latitude, longitude
                FROM cities_ibge
                WHERE UPPER(name) = UPPER(?) AND UPPER(state_code) = UPPER(?)
                AND latitude IS NOT NULL AND longitude IS NOT NULL
                LIMIT 1
            """, (city, state))

            result = cursor.fetchone()
            if result and result[0] and result[1]:
                return (result[0], result[1])

            # 3. Fallback: GeoNames (capitais ou cidades grandes)
            cursor = conn.execute("""
                SELECT latitude, longitude
                FROM neighborhoods_geonames
                WHERE UPPER(name) = UPPER(?) AND state_code = ?
                AND feature_code IN ('PPLA', 'PPLA2', 'PPLA3', 'PPL')
                ORDER BY population DESC
                LIMIT 1
            """, (city, state))

            result = cursor.fetchone()
            if result and result[0] and result[1]:
                return (result[0], result[1])

            return None

        except Exception as e:
            self.logger.error(f"[GEONAMES] ❌ Erro ao buscar coordenadas de {city}/{state}: {e}")
            return None

    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calcula distância entre dois pontos usando fórmula de Haversine
        Retorna distância em quilômetros
        """
        from math import radians, sin, cos, sqrt, asin

        # Converter para radianos
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Fórmula de Haversine
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))

        # Raio da Terra em km
        r = 6371

        return round(c * r, 2)

    def set_neighborhoods(self, city: str, state: str, neighborhoods: List[str], source: str = 'geonames'):
        """Armazena bairros no cache (mantido para compatibilidade, mas GeoNames é a fonte primária)"""
        # GeoNames é a fonte primária agora, este método é legacy
        pass

    def get_stats(self) -> dict:
        """Retorna estatísticas do cache GeoNames"""
        try:
            conn = self._get_connection()

            # Total de locais no GeoNames
            cursor = conn.execute("""
                SELECT COUNT(DISTINCT state_code) as total_states,
                       COUNT(*) as total_places,
                       COUNT(DISTINCT admin2_code) as total_cities
                FROM neighborhoods_geonames
            """)
            row = cursor.fetchone()

            if row:
                return {
                    'total_states': row[0],
                    'total_places': row[1],
                    'total_cities': row[2],
                    'source': 'GeoNames (offline)'
                }

        except Exception:
            pass

        return {'total_states': 0, 'total_places': 0, 'total_cities': 0, 'source': 'none'}

    def clear_old_entries(self, days: int = 90):
        """GeoNames não expira, retorna 0"""
        return 0
