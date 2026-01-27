"""
Cache de Coordenadas de Cidades Brasileiras
Usa banco unificado cache.db
"""
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class CitiesCoordinatesCache:
    """Cache de coordenadas de cidades brasileiras para geocodificação instantânea"""

    def __init__(self):
        self.cache_dir = Path("data/cache")
        self.db_path = self.cache_dir / "cache.db"  # ✅ Banco unificado
        self._ensure_coordinates_column()

    def _ensure_coordinates_column(self):
        """Garante que a tabela de cidades tem colunas de coordenadas"""
        if not self.db_path.exists():
            return

        try:
            conn = sqlite3.connect(self.db_path)

            # Verificar se colunas já existem
            cursor = conn.execute("PRAGMA table_info(cities)")
            columns = [row[1] for row in cursor.fetchall()]

            if 'latitude' not in columns:
                conn.execute("ALTER TABLE cities ADD COLUMN latitude REAL")
            if 'longitude' not in columns:
                conn.execute("ALTER TABLE cities ADD COLUMN longitude REAL")

            # Criar índice para buscas rápidas
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_cities_search 
                ON cities(name, state)
            """)

            conn.commit()
            conn.close()
        except Exception:
            pass

    def get_city_coordinates(self, city: str, state: str) -> Optional[Tuple[float, float]]:
        """Busca coordenadas de uma cidade no cache"""
        if not self.db_path.exists():
            return None

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("""
                SELECT latitude, longitude 
                FROM cities 
                WHERE LOWER(name) = LOWER(?) 
                AND LOWER(state) = LOWER(?)
                AND latitude IS NOT NULL 
                AND longitude IS NOT NULL
                LIMIT 1
            """, (city.strip(), state.strip()))

            row = cursor.fetchone()
            conn.close()

            if row and row[0] and row[1]:
                return (float(row[0]), float(row[1]))

            return None
        except Exception:
            return None

    def set_city_coordinates(self, city: str, state: str, latitude: float, longitude: float):
        """Armazena coordenadas de uma cidade no cache"""
        if not self.db_path.exists():
            return

        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                UPDATE cities 
                SET latitude = ?, longitude = ?
                WHERE LOWER(name) = LOWER(?) 
                AND LOWER(state) = LOWER(?)
            """, (latitude, longitude, city.strip(), state.strip()))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def get_all_cities_with_coords(self) -> List[Dict]:
        """Retorna todas as cidades com coordenadas"""
        if not self.db_path.exists():
            return []

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT name, state, latitude, longitude, population
                FROM cities 
                WHERE latitude IS NOT NULL 
                AND longitude IS NOT NULL
                ORDER BY population DESC
            """)

            cities = []
            for row in cursor:
                cities.append({
                    'name': row['name'],
                    'state': row['state'],
                    'lat': row['latitude'],
                    'lon': row['longitude'],
                    'population': row['population']
                })

            conn.close()
            return cities
        except Exception:
            return []

    def get_cache_stats(self) -> dict:
        """Retorna estatísticas do cache de coordenadas"""
        if not self.db_path.exists():
            return {'total': 0, 'with_coords': 0, 'coverage': 0}

        try:
            conn = sqlite3.connect(self.db_path)

            cursor = conn.execute("SELECT COUNT(*) FROM cities")
            total = cursor.fetchone()[0]

            cursor = conn.execute("""
                SELECT COUNT(*) FROM cities 
                WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            """)
            with_coords = cursor.fetchone()[0]

            conn.close()

            coverage = (with_coords / total * 100) if total > 0 else 0

            return {
                'total': total,
                'with_coords': with_coords,
                'coverage': round(coverage, 1)
            }
        except Exception:
            return {'total': 0, 'with_coords': 0, 'coverage': 0}

    def preload_major_cities_coordinates(self):
        """Pré-carrega coordenadas das principais cidades brasileiras"""
        # Coordenadas das capitais e principais cidades
        major_cities = {
            ('São Paulo', 'SP'): (-23.5505, -46.6333),
            ('Rio de Janeiro', 'RJ'): (-22.9068, -43.1729),
            ('Brasília', 'DF'): (-15.8267, -47.9218),
            ('Salvador', 'BA'): (-12.9714, -38.5014),
            ('Fortaleza', 'CE'): (-3.7172, -38.5433),
            ('Belo Horizonte', 'MG'): (-19.9167, -43.9345),
            ('Manaus', 'AM'): (-3.1190, -60.0217),
            ('Curitiba', 'PR'): (-25.4284, -49.2733),
            ('Recife', 'PE'): (-8.0476, -34.8770),
            ('Porto Alegre', 'RS'): (-30.0346, -51.2177),
            ('Belém', 'PA'): (-1.4558, -48.5039),
            ('Goiânia', 'GO'): (-16.6869, -49.2648),
            ('Guarulhos', 'SP'): (-23.4538, -46.5333),
            ('Campinas', 'SP'): (-22.9099, -47.0626),
            ('São Luís', 'MA'): (-2.5387, -44.2825),
            ('São Gonçalo', 'RJ'): (-22.8268, -43.0539),
            ('Maceió', 'AL'): (-9.6658, -35.7353),
            ('Duque de Caxias', 'RJ'): (-22.7858, -43.3055),
            ('Natal', 'RN'): (-5.7945, -35.2110),
            ('Teresina', 'PI'): (-5.0892, -42.8019),
            ('Campo Grande', 'MS'): (-20.4697, -54.6201),
            ('Nova Iguaçu', 'RJ'): (-22.7592, -43.4511),
            ('São Bernardo do Campo', 'SP'): (-23.6914, -46.5646),
            ('João Pessoa', 'PB'): (-7.1195, -34.8450),
            ('Santo André', 'SP'): (-23.6636, -46.5341),
            ('Osasco', 'SP'): (-23.5329, -46.7920),
            ('Jaboatão dos Guararapes', 'PE'): (-8.1120, -35.0145),
            ('São José dos Campos', 'SP'): (-23.1790, -45.8869),
            ('Ribeirão Preto', 'SP'): (-21.1704, -47.8103),
            ('Uberlândia', 'MG'): (-18.9186, -48.2772),
            ('Sorocaba', 'SP'): (-23.5003, -47.4583),
            ('Contagem', 'MG'): (-19.9320, -44.0537),
            ('Aracaju', 'SE'): (-10.9091, -37.0677),
            ('Feira de Santana', 'BA'): (-12.2664, -38.9663),
            ('Cuiabá', 'MT'): (-15.6014, -56.0979),
            ('Joinville', 'SC'): (-26.3044, -48.8487),
            ('Juiz de Fora', 'MG'): (-21.7642, -43.3502),
            ('Londrina', 'PR'): (-23.3045, -51.1696),
            ('Aparecida de Goiânia', 'GO'): (-16.8173, -49.2437),
            ('Niterói', 'RJ'): (-22.8833, -43.1036),
            ('Ananindeua', 'PA'): (-1.3656, -48.3722),
            ('Belford Roxo', 'RJ'): (-22.7642, -43.3997),
            ('Caxias do Sul', 'RS'): (-29.1634, -51.1797),
            ('Florianópolis', 'SC'): (-27.5954, -48.5480),
            ('Santos', 'SP'): (-23.9608, -46.3334),
            ('Vitória', 'ES'): (-20.3155, -40.3128),
            ('Mauá', 'SP'): (-23.6678, -46.4614),
            ('Carapicuíba', 'SP'): (-23.5225, -46.8356),
            ('Diadema', 'SP'): (-23.6858, -46.6230),
            ('Piracicaba', 'SP'): (-22.7253, -47.6492),
        }

        if not self.db_path.exists():
            return

        saved = 0
        try:
            for (city, state), (lat, lon) in major_cities.items():
                self.set_city_coordinates(city, state, lat, lon)
                saved += 1

            if saved > 0:
                print(f"[CACHE] ✅ {saved} cidades principais pré-carregadas com coordenadas")
        except Exception as e:
            print(f"[CACHE] ⚠️ Erro ao pré-carregar coordenadas: {e}")
