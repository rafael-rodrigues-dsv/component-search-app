"""
Serviço para gerenciar coordenadas de municípios IBGE
Fornece lookup instantâneo de coordenadas sem chamadas externas
"""
import sqlite3
from pathlib import Path
from typing import Optional, Tuple
import requests


class IBGECoordinatesService:
    """Serviço para coordenadas pré-calculadas de municípios brasileiros"""

    def __init__(self):
        self.db_path = Path("data/cache/pythonsearchcache.db")
        # Tabela municipalities_coordinates já criada por create_cache_db.py

    def get_coordinates(self, city: str, state: str) -> Optional[Tuple[float, float]]:
        """Obter coordenadas de uma cidade do banco local (instantâneo)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT latitude, longitude 
                FROM municipalities_coordinates 
                WHERE LOWER(city) = LOWER(?) AND UPPER(state) = UPPER(?)
            """, (city, state))

            result = cursor.fetchone()
            conn.close()

            if result:
                return (result[0], result[1])

            return None

        except Exception as e:
            print(f"[IBGE-COORDS] Erro ao buscar coordenadas: {e}")
            return None

    def set_coordinates(self, city: str, state: str, lat: float, lng: float, ibge_code: str = None):
        """Salvar coordenadas no banco local"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO municipalities_coordinates 
                (city, state, latitude, longitude, ibge_code)
                VALUES (?, ?, ?, ?, ?)
            """, (city, state, lat, lng, ibge_code))

            conn.commit()
            conn.close()

        except Exception as e:
            print(f"[IBGE-COORDS] Erro ao salvar coordenadas: {e}")

    def load_ibge_municipalities(self) -> int:
        """
        Carregar TODOS os municípios brasileiros do IBGE com coordenadas
        Retorna quantidade de municípios carregados
        """
        try:
            # Verificar se já tem dados
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM municipalities_coordinates")
            count = cursor.fetchone()[0]
            conn.close()

            if count > 5000:
                print(f"[IBGE-COORDS] ✅ Já existem {count} municípios carregados")
                return count

            print("[IBGE-COORDS] 🚀 Carregando municípios do IBGE com coordenadas...")

            # Buscar TODOS os municípios do Brasil
            url = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios"
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            municipalities = response.json()
            print(f"[IBGE-COORDS] 📥 {len(municipalities)} municípios obtidos do IBGE")

            # Buscar coordenadas via GeoNames (público e gratuito)
            # Ou usar coordenadas aproximadas baseadas no centro do estado
            loaded = 0

            # Coordenadas das capitais e principais cidades (pré-calculadas)
            known_coords = self._get_known_coordinates()

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for i, mun in enumerate(municipalities):
                try:
                    city_name = mun.get('nome')
                    if not city_name:
                        continue

                    # Tentar obter UF de diferentes estruturas possíveis
                    state_uf = None
                    if 'microrregiao' in mun and mun['microrregiao']:
                        if 'mesorregiao' in mun['microrregiao'] and mun['microrregiao']['mesorregiao']:
                            if 'UF' in mun['microrregiao']['mesorregiao'] and mun['microrregiao']['mesorregiao']['UF']:
                                state_uf = mun['microrregiao']['mesorregiao']['UF'].get('sigla')

                    # Fallback: tentar outras estruturas
                    if not state_uf and 'regiao-imediata' in mun:
                        if 'regiao-intermediaria' in mun['regiao-imediata']:
                            if 'UF' in mun['regiao-imediata']['regiao-intermediaria']:
                                state_uf = mun['regiao-imediata']['regiao-intermediaria']['UF'].get('sigla')

                    if not state_uf:
                        # Pular municípios sem UF
                        continue

                    ibge_code = str(mun.get('id', ''))

                    # Tentar coordenadas conhecidas primeiro
                    key = (city_name.lower(), state_uf.upper())
                    if key in known_coords:
                        lat, lng = known_coords[key]
                        cursor.execute("""
                            INSERT OR IGNORE INTO municipalities_coordinates 
                            (city, state, latitude, longitude, ibge_code)
                            VALUES (?, ?, ?, ?, ?)
                        """, (city_name, state_uf, lat, lng, ibge_code))
                        loaded += 1
                    else:
                        # Para cidades sem coordenadas, adicionar apenas o registro
                        # As coordenadas serão obtidas via Photon quando necessário
                        cursor.execute("""
                            INSERT OR IGNORE INTO municipalities_coordinates 
                            (city, state, latitude, longitude, ibge_code)
                            VALUES (?, ?, ?, ?, ?)
                        """, (city_name, state_uf, 0.0, 0.0, ibge_code))

                    if (i + 1) % 1000 == 0:
                        print(f"[IBGE-COORDS] 📊 Processados {i + 1}/{len(municipalities)} municípios...")
                        conn.commit()

                except Exception as e:
                    # Log erro mas continua processamento
                    if i % 1000 == 0:
                        print(f"[IBGE-COORDS] ⚠️  Erro no município {i+1}: {e}")
                    continue

            conn.commit()
            conn.close()

            print(f"[IBGE-COORDS] ✅ {loaded} municípios carregados com coordenadas")
            print(f"[IBGE-COORDS] ℹ️  {len(municipalities) - loaded} municípios sem coordenadas (usarão Photon)")

            # Carregar bairros das principais cidades (com coordenadas conhecidas)
            if loaded > 0:
                self._load_neighborhoods_for_main_cities(list(known_coords.keys()))

            return len(municipalities)

        except Exception as e:
            print(f"[IBGE-COORDS] ❌ Erro ao carregar municípios: {e}")
            return 0

    def _get_known_coordinates(self) -> dict:
        """Retorna coordenadas conhecidas das principais cidades brasileiras"""
        return {
            # Capitais
            ('são paulo', 'SP'): (-23.5505, -46.6333),
            ('rio de janeiro', 'RJ'): (-22.9068, -43.1729),
            ('brasília', 'DF'): (-15.8267, -47.9218),
            ('salvador', 'BA'): (-12.9714, -38.5014),
            ('fortaleza', 'CE'): (-3.7172, -38.5433),
            ('belo horizonte', 'MG'): (-19.9167, -43.9345),
            ('manaus', 'AM'): (-3.1190, -60.0217),
            ('curitiba', 'PR'): (-25.4284, -49.2733),
            ('recife', 'PE'): (-8.0476, -34.8770),
            ('porto alegre', 'RS'): (-30.0346, -51.2177),
            ('belém', 'PA'): (-1.4558, -48.5039),
            ('goiânia', 'GO'): (-16.6869, -49.2648),
            ('são luís', 'MA'): (-2.5387, -44.2825),
            ('maceió', 'AL'): (-9.6658, -35.7353),
            ('natal', 'RN'): (-5.7945, -35.2110),
            ('teresina', 'PI'): (-5.0892, -42.8019),
            ('campo grande', 'MS'): (-20.4697, -54.6201),
            ('joão pessoa', 'PB'): (-7.1195, -34.8450),
            ('aracaju', 'SE'): (-10.9091, -37.0677),
            ('cuiabá', 'MT'): (-15.6014, -56.0979),
            ('florianópolis', 'SC'): (-27.5954, -48.5480),
            ('vitória', 'ES'): (-20.3155, -40.3128),
            ('porto velho', 'RO'): (-8.7619, -63.9039),
            ('boa vista', 'RR'): (2.8235, -60.6758),
            ('macapá', 'AP'): (0.0349, -51.0694),
            ('rio branco', 'AC'): (-9.9747, -67.8100),
            ('palmas', 'TO'): (-10.1840, -48.3336),

            # Principais cidades SP
            ('guarulhos', 'SP'): (-23.4538, -46.5333),
            ('campinas', 'SP'): (-22.9099, -47.0626),
            ('são bernardo do campo', 'SP'): (-23.6914, -46.5646),
            ('santo andré', 'SP'): (-23.6636, -46.5341),
            ('osasco', 'SP'): (-23.5329, -46.7920),
            ('são josé dos campos', 'SP'): (-23.1790, -45.8869),
            ('ribeirão preto', 'SP'): (-21.1704, -47.8103),
            ('sorocaba', 'SP'): (-23.5003, -47.4583),
            ('santos', 'SP'): (-23.9608, -46.3334),
            ('mauá', 'SP'): (-23.6678, -46.4614),
            ('carapicuíba', 'SP'): (-23.5225, -46.8356),
            ('diadema', 'SP'): (-23.6858, -46.6230),
            ('piracicaba', 'SP'): (-22.7253, -47.6492),

            # Principais cidades RJ
            ('niterói', 'RJ'): (-22.8833, -43.1036),
            ('nova iguaçu', 'RJ'): (-22.7592, -43.4511),
            ('duque de caxias', 'RJ'): (-22.7858, -43.3055),
            ('são gonçalo', 'RJ'): (-22.8268, -43.0539),
            ('belford roxo', 'RJ'): (-22.7642, -43.3997),

            # Principais cidades MG
            ('contagem', 'MG'): (-19.9320, -44.0537),
            ('uberlândia', 'MG'): (-18.9186, -48.2772),
            ('juiz de fora', 'MG'): (-21.7642, -43.3502),

            # Principais cidades RS
            ('caxias do sul', 'RS'): (-29.1634, -51.1797),
            ('canoas', 'RS'): (-29.9177, -51.1836),

            # Principais cidades PR
            ('londrina', 'PR'): (-23.3045, -51.1696),
            ('maringá', 'PR'): (-23.4205, -51.9333),

            # Principais cidades BA
            ('feira de santana', 'BA'): (-12.2664, -38.9663),
            ('vitória da conquista', 'BA'): (-14.8615, -40.8442),

            # Principais cidades PE
            ('jaboatão dos guararapes', 'PE'): (-8.1120, -35.0145),
            ('olinda', 'PE'): (-8.0089, -34.8553),

            # Principais cidades CE
            ('caucaia', 'CE'): (-3.7361, -38.6531),
            ('juazeiro do norte', 'CE'): (-7.2131, -39.3151),

            # Principais cidades GO
            ('aparecida de goiânia', 'GO'): (-16.8173, -49.2437),

            # Principais cidades PA
            ('ananindeua', 'PA'): (-1.3656, -48.3722),

            # Principais cidades SC
            ('joinville', 'SC'): (-26.3044, -48.8487),
        }

    def get_stats(self) -> dict:
        """Obter estatísticas do banco de coordenadas"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM municipalities_coordinates")
            total = cursor.fetchone()[0]

            cursor.execute("""
                SELECT COUNT(*) FROM municipalities_coordinates 
                WHERE latitude != 0.0 AND longitude != 0.0
            """)
            with_coords = cursor.fetchone()[0]

            conn.close()

            return {
                'total': total,
                'with_coords': with_coords,
                'without_coords': total - with_coords
            }

        except Exception as e:
            print(f"[IBGE-COORDS] Erro ao obter stats: {e}")
            return {'total': 0, 'with_coords': 0, 'without_coords': 0}

    def _load_neighborhoods_for_main_cities(self, cities_list: list):
        """Carregar bairros das principais cidades via Photon/Nominatim"""
        try:
            print(f"[IBGE-COORDS] 🏘️  Carregando bairros das {len(cities_list)} principais cidades...")

            import time
            loaded_count = 0

            for i, (city_lower, state_uf) in enumerate(cities_list):
                try:
                    # Verificar se já tem bairros no cache
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()

                    cursor.execute("""
                        SELECT COUNT(*) FROM neighborhoods_cache 
                        WHERE LOWER(city) = ? AND UPPER(state) = ?
                    """, (city_lower, state_uf))

                    count = cursor.fetchone()[0]
                    conn.close()

                    if count > 0:
                        continue  # Já tem bairros

                    # Buscar bairros via GeoNames (offline)
                    city_name = city_lower.title()  # Capitalizar
                    neighborhoods = self._get_neighborhoods_from_geonames(city_name, state_uf)

                    if neighborhoods and len(neighborhoods) > 0:
                        loaded_count += 1

                        if (i + 1) % 10 == 0:
                            print(f"[IBGE-COORDS] 📊 Carregados bairros de {i + 1}/{len(cities_list)} cidades...")

                except Exception as e:
                    continue

            print(f"[IBGE-COORDS] ✅ Bairros carregados para {loaded_count} cidades principais (GeoNames offline)")

        except Exception as e:
            print(f"[IBGE-COORDS] ⚠️  Erro ao carregar bairros: {e}")

    def _get_neighborhoods_from_geonames(self, city: str, state: str) -> list:
        """Buscar bairros via GeoNames (100% offline)"""
        try:
            from src.infrastructure.cache.neighborhoods_cache import NeighborhoodsCache

            cache = NeighborhoodsCache()
            neighborhoods_data = cache.get_neighborhoods_from_geonames(city, state, limit=20)

            if neighborhoods_data:
                # Extrair apenas nomes
                neighborhoods = [n['name'] for n in neighborhoods_data if n['name'].lower() != city.lower()]
                return list(set(neighborhoods))  # Remover duplicatas

            # Fallback: retornar nome da cidade
            return [city]

        except Exception as e:
            return [city]  # Fallback: retornar nome da cidade


