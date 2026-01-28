#!/usr/bin/env python3
"""
Serviço de cache geográfico - acesso rápido aos dados IBGE locais
"""
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import time
import math


class GeographicCacheService:
    """Serviço para acesso rápido aos dados geográficos em cache"""

    def __init__(self):
        # Determinar pasta do projeto
        import os
        if 'src' in os.getcwd() or 'scripts' in os.getcwd():
            # Subir até a raiz do projeto
            current = Path.cwd()
            while current.name in ['src', 'scripts', 'infrastructure', 'cache']:
                current = current.parent
            project_root = current
        else:
            project_root = Path.cwd()

        cache_dir = project_root / "data" / "cache"
        self.db_path = cache_dir / "pythonsearchcache.db"

        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Banco de cache não encontrado em {self.db_path}\n"
                f"Execute o robô normalmente - os dados geográficos serão carregados automaticamente\n"
                f"(GeographicLoadApplicationService é executado no InitializeDatabaseService)"
            )

    def _get_connection(self) -> sqlite3.Connection:
        """Retorna conexão com o banco"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Retorna resultados como dict
        return conn

    # ========== ESTADOS ==========

    def get_state_by_code(self, code: str) -> Optional[Dict]:
        """Busca estado por código (ex: 'SP', 'RJ')"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM states_ibge WHERE code = ?
        """, (code.upper(),))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_all_states(self) -> List[Dict]:
        """Retorna todos os estados"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM states_ibge ORDER BY name")
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_nearby_states(self, origin_state_code: str, max_distance_km: int) -> List[str]:
        """
        Retorna códigos de estados vizinhos baseado em distância entre capitais

        Args:
            origin_state_code: Código do estado origem (ex: 'SP')
            max_distance_km: Distância máxima em km

        Returns:
            Lista de códigos de estados (ex: ['SP', 'RJ', 'MG', 'PR'])
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Buscar coordenadas da capital do estado origem
        cursor.execute("""
            SELECT capital_lat, capital_lon 
            FROM states_ibge 
            WHERE code = ?
        """, (origin_state_code.upper(),))

        origin = cursor.fetchone()
        if not origin or not origin['capital_lat']:
            conn.close()
            return [origin_state_code.upper()]

        origin_lat, origin_lon = origin['capital_lat'], origin['capital_lon']

        # Buscar todos os estados
        cursor.execute("""
            SELECT code, capital_lat, capital_lon 
            FROM states_ibge 
            WHERE capital_lat IS NOT NULL
        """)

        states = cursor.fetchall()
        conn.close()

        # Calcular distâncias
        nearby_states = []
        for state in states:
            state_code = state['code']

            # Estado origem sempre inclui
            if state_code == origin_state_code.upper():
                nearby_states.append(state_code)
                continue

            # Calcular distância entre capitais
            distance = self._calculate_haversine(
                origin_lat, origin_lon,
                state['capital_lat'], state['capital_lon']
            )

            if distance <= max_distance_km:
                nearby_states.append(state_code)

        return nearby_states

    # ========== CIDADES ==========

    def get_cities_by_state(
        self,
        state_code: str,
        min_population: Optional[int] = None,
        only_with_coordinates: bool = False
    ) -> List[Dict]:
        """
        Busca cidades de um estado

        Args:
            state_code: Código do estado (ex: 'SP')
            min_population: População mínima (opcional)
            only_with_coordinates: Apenas cidades geocodificadas

        Returns:
            Lista de dicionários com dados das cidades
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM cities_ibge WHERE state_code = ?"
        params = [state_code.upper()]

        if min_population is not None:
            query += " AND population >= ?"
            params.append(min_population)

        if only_with_coordinates:
            query += " AND latitude IS NOT NULL AND longitude IS NOT NULL"

        query += " ORDER BY population DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_city_by_ibge_code(self, ibge_code: str) -> Optional[Dict]:
        """Busca cidade por código IBGE"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM cities_ibge WHERE ibge_code = ?
        """, (str(ibge_code),))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def get_city_by_name_and_state(self, city_name: str, state_code: str) -> Optional[Dict]:
        """Busca cidade por nome e estado"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM cities_ibge 
            WHERE name = ? AND state_code = ?
        """, (city_name, state_code.upper()))

        row = cursor.fetchone()
        conn.close()

        if row:
            return dict(row)
        return None

    def update_city_coordinates(
        self,
        ibge_code: str,
        latitude: float,
        longitude: float,
        source: str = 'Nominatim',
        quality: str = 'HIGH'
    ):
        """Atualiza coordenadas de uma cidade"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE cities_ibge 
            SET latitude = ?, longitude = ?, 
                geo_source = ?, geo_quality = ?,
                updated_at = ?
            WHERE ibge_code = ?
        """, (latitude, longitude, source, quality, int(time.time()), str(ibge_code)))

        conn.commit()
        conn.close()

    def update_city_population(self, ibge_code: str, population: int):
        """Atualiza população de uma cidade"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE cities_ibge 
            SET population = ?, updated_at = ?
            WHERE ibge_code = ?
        """, (population, int(time.time()), str(ibge_code)))

        conn.commit()
        conn.close()

    # ========== DISTÂNCIAS ==========

    def get_distance(self, origin_ibge: str, dest_ibge: str) -> Optional[float]:
        """
        Busca distância entre duas cidades (cache)

        Returns:
            Distância em km ou None se não encontrada
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Tentar buscar nos dois sentidos
        cursor.execute("""
            SELECT distance_km FROM distance_matrix 
            WHERE (origin_city_ibge = ? AND dest_city_ibge = ?)
               OR (origin_city_ibge = ? AND dest_city_ibge = ?)
            LIMIT 1
        """, (str(origin_ibge), str(dest_ibge), str(dest_ibge), str(origin_ibge)))

        row = cursor.fetchone()
        conn.close()

        if row:
            return row['distance_km']
        return None

    def save_distance(
        self,
        origin_ibge: str,
        dest_ibge: str,
        distance_km: float,
        method: str = 'HAVERSINE'
    ):
        """Salva distância no cache"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Verificar se cidades estão no mesmo estado
        cursor.execute("""
            SELECT state_code FROM cities_ibge WHERE ibge_code = ?
        """, (str(origin_ibge),))
        origin_state = cursor.fetchone()

        cursor.execute("""
            SELECT state_code FROM cities_ibge WHERE ibge_code = ?
        """, (str(dest_ibge),))
        dest_state = cursor.fetchone()

        is_same_state = 0
        if origin_state and dest_state:
            is_same_state = 1 if origin_state['state_code'] == dest_state['state_code'] else 0

        # Inserir ou atualizar
        cursor.execute("""
            INSERT OR REPLACE INTO distance_matrix (
                origin_city_ibge, dest_city_ibge, distance_km,
                calculation_method, is_same_state, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            str(origin_ibge), str(dest_ibge), round(distance_km, 2),
            method, is_same_state, int(time.time())
        ))

        conn.commit()
        conn.close()

    def get_cities_within_radius(
        self,
        origin_ibge: str,
        radius_km: float,
        min_population: Optional[int] = None
    ) -> List[Dict]:
        """
        Busca cidades dentro de um raio (usando cache de distâncias)

        Args:
            origin_ibge: Código IBGE da cidade origem
            radius_km: Raio em km
            min_population: População mínima (opcional)

        Returns:
            Lista de cidades com distância
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        query = """
            SELECT 
                c.*,
                d.distance_km
            FROM cities_ibge c
            JOIN distance_matrix d ON (
                (d.origin_city_ibge = ? AND d.dest_city_ibge = c.ibge_code)
                OR (d.dest_city_ibge = ? AND d.origin_city_ibge = c.ibge_code)
            )
            WHERE d.distance_km <= ?
        """
        params = [str(origin_ibge), str(origin_ibge), radius_km]

        if min_population is not None:
            query += " AND c.population >= ?"
            params.append(min_population)

        query += " ORDER BY d.distance_km"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    # ========== BAIRROS ==========

    def get_neighborhoods_by_city(self, city_ibge_code: str) -> List[Dict]:
        """Busca bairros de uma cidade"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM neighborhoods_ibge 
            WHERE city_ibge_code = ?
            ORDER BY name
        """, (str(city_ibge_code),))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def save_neighborhood(
        self,
        name: str,
        city_ibge_code: str,
        city_name: str,
        state_code: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        ibge_code: Optional[str] = None,
        source: str = 'IBGE'
    ):
        """Salva bairro no cache"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO neighborhoods_ibge (
                ibge_code, name, city_ibge_code, city_name, state_code,
                latitude, longitude, geo_source, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ibge_code, name, str(city_ibge_code), city_name, state_code,
            latitude, longitude, source, int(time.time()), int(time.time())
        ))

        conn.commit()
        conn.close()

    # ========== UTILS ==========

    def _calculate_haversine(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calcula distância entre dois pontos usando fórmula de Haversine

        Returns:
            Distância em quilômetros
        """
        R = 6371.0  # Raio da Terra em km

        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        distance = R * c
        return distance

    def get_stats(self) -> Dict:
        """Retorna estatísticas do cache geográfico"""
        conn = self._get_connection()
        cursor = conn.cursor()

        stats = {}

        # Estados
        cursor.execute("SELECT COUNT(*) as total FROM states_ibge")
        stats['states'] = cursor.fetchone()['total']

        # Cidades
        cursor.execute("SELECT COUNT(*) as total FROM cities_ibge")
        stats['cities_total'] = cursor.fetchone()['total']

        cursor.execute("""
            SELECT COUNT(*) as total FROM cities_ibge 
            WHERE latitude IS NOT NULL
        """)
        stats['cities_geocoded'] = cursor.fetchone()['total']

        cursor.execute("""
            SELECT COUNT(*) as total FROM cities_ibge 
            WHERE is_capital = 1
        """)
        stats['capitals'] = cursor.fetchone()['total']

        # Bairros
        cursor.execute("SELECT COUNT(*) as total FROM neighborhoods_ibge")
        stats['neighborhoods'] = cursor.fetchone()['total']

        # Distâncias
        cursor.execute("SELECT COUNT(*) as total FROM distance_matrix")
        stats['cached_distances'] = cursor.fetchone()['total']

        conn.close()

        return stats


# Singleton instance
_instance: Optional[GeographicCacheService] = None

def get_geographic_cache() -> GeographicCacheService:
    """Retorna instância singleton do cache geográfico"""
    global _instance
    if _instance is None:
        _instance = GeographicCacheService()
    return _instance


if __name__ == "__main__":
    # Teste do serviço
    print("🗺️  Teste do Serviço de Cache Geográfico")
    print("=" * 60)

    try:
        cache = GeographicCacheService()

        # Estatísticas
        stats = cache.get_stats()
        print(f"\n📊 Estatísticas:")
        print(f"   Estados: {stats['states']}")
        print(f"   Municípios: {stats['cities_total']}")
        print(f"   Geocodificados: {stats['cities_geocoded']}")
        print(f"   Capitais: {stats['capitals']}")
        print(f"   Bairros: {stats['neighborhoods']}")
        print(f"   Distâncias em cache: {stats['cached_distances']}")

        # Teste: buscar estado
        print(f"\n🔍 Teste 1: Buscar estado SP")
        sp = cache.get_state_by_code('SP')
        if sp:
            print(f"   ✅ {sp['name']} - Capital: {sp['capital_city']}")

        # Teste: cidades de SP com pop > 500k
        print(f"\n🔍 Teste 2: Cidades de SP com população > 500k")
        cities = cache.get_cities_by_state('SP', min_population=500000)
        print(f"   ✅ {len(cities)} cidades encontradas")
        for city in cities[:5]:
            print(f"      - {city['name']}: {city['population']:,} hab")

        # Teste: estados vizinhos de SP (500km)
        print(f"\n🔍 Teste 3: Estados vizinhos de SP (raio 500km)")
        nearby = cache.get_nearby_states('SP', 500)
        print(f"   ✅ Estados: {', '.join(nearby)}")

        print(f"\n✅ Todos os testes passaram!")

    except FileNotFoundError as e:
        print(f"\n❌ Erro: {e}")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
