"""
Serviço para carregar dados geográficos do GeoNames (100% offline após download inicial)
Substitui Nominatim para busca de bairros e coordenadas
"""
import sqlite3
import zipfile
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging


class GeoNamesService:
    """Serviço para download e cache de dados GeoNames (bairros brasileiros)"""

    GEONAMES_URL = "https://download.geonames.org/export/dump/BR.zip"
    CACHE_DB = Path("data/cache/pythonsearchcache.db")
    GEONAMES_FILE = Path("data/cache/BR.txt")

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        """Garante que diretório de cache existe"""
        self.CACHE_DB.parent.mkdir(parents=True, exist_ok=True)

    def is_data_loaded(self) -> bool:
        """Verifica se dados GeoNames já foram carregados"""
        if not self.CACHE_DB.exists():
            return False

        try:
            conn = sqlite3.connect(self.CACHE_DB)
            cursor = conn.cursor()

            # Verificar se a tabela existe primeiro
            cursor.execute("""
                SELECT COUNT(*) FROM sqlite_master 
                WHERE type='table' AND name='neighborhoods_geonames'
            """)
            table_exists = cursor.fetchone()[0] > 0

            if not table_exists:
                conn.close()
                return False

            # Agora sim, verificar se tem dados
            cursor.execute("SELECT COUNT(*) FROM neighborhoods_geonames")
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except Exception:
            return False

    def download_and_load(self) -> bool:
        """
        Baixa dados do GeoNames e carrega no cache SQLite
        Retorna True se sucesso
        """
        try:
            self.logger.info("[GEONAMES] 🌎 Baixando dados do Brasil (GeoNames)...")
            self.logger.info("[GEONAMES] 📦 URL: https://download.geonames.org/export/dump/BR.zip")
            self.logger.info("[GEONAMES] ⏳ Aguarde, pode levar 2-5 minutos...")

            # Download do arquivo ZIP
            zip_path = self.CACHE_DB.parent / "BR.zip"

            response = requests.get(self.GEONAMES_URL, stream=True, timeout=60)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(zip_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            if downloaded % (1024 * 1024) == 0:  # A cada 1MB
                                self.logger.info(f"[GEONAMES] 📥 Baixando... {percent:.1f}%")

            self.logger.info("[GEONAMES] ✅ Download concluído!")

            # Extrair arquivo TXT
            self.logger.info("[GEONAMES] 📂 Extraindo dados...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extract('BR.txt', self.CACHE_DB.parent)

            self.logger.info("[GEONAMES] ✅ Extração concluída!")

            # Carregar no banco
            self._load_to_database()

            # Limpar arquivos temporários
            zip_path.unlink()
            self.GEONAMES_FILE.unlink()

            self.logger.info("[GEONAMES] 🎉 Carga completa! Dados offline disponíveis.")
            return True

        except Exception as e:
            self.logger.error(f"[GEONAMES] ❌ Erro ao baixar/carregar dados: {e}")
            return False

    def _load_to_database(self):
        """Carrega arquivo BR.txt no SQLite (tabela já criada por create_cache_db.py)"""
        self.logger.info("[GEONAMES] 💾 Carregando dados no cache SQLite...")

        conn = sqlite3.connect(self.CACHE_DB)
        cursor = conn.cursor()

        # Limpar dados antigos (tabela já existe - criada por create_cache_db.py)
        cursor.execute("DELETE FROM neighborhoods_geonames")

        inserted = 0
        skipped = 0

        with open(self.GEONAMES_FILE, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line_num % 10000 == 0:
                    self.logger.info(f"[GEONAMES] 📊 Processando linha {line_num:,}...")

                try:
                    parts = line.strip().split('\t')
                    if len(parts) < 19:
                        continue

                    geonameid = int(parts[0])
                    name = parts[1]
                    asciiname = parts[2]
                    latitude = float(parts[4])
                    longitude = float(parts[5])
                    feature_class = parts[6]
                    feature_code = parts[7]
                    country_code = parts[8]
                    admin1_code = parts[10]  # Estado (SP, RJ, MG...)
                    admin2_code = parts[11]  # Código município IBGE
                    population = int(parts[14]) if parts[14] else 0
                    elevation = int(parts[15]) if parts[15] else None
                    timezone = parts[17]

                    # Filtrar apenas locais relevantes (cidades, bairros, distritos)
                    # PPL = populated place, PPLX = section of populated place
                    if feature_code not in ('PPL', 'PPLX', 'PPLA', 'PPLA2', 'PPLA3', 'PPLA4', 'PPLC'):
                        skipped += 1
                        continue

                    cursor.execute("""
                        INSERT OR REPLACE INTO neighborhoods_geonames 
                        (geonameid, name, asciiname, latitude, longitude, feature_class, feature_code,
                         country_code, admin1_code, admin2_code, state_code, population, elevation, timezone)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (geonameid, name, asciiname, latitude, longitude, feature_class, feature_code,
                          country_code, admin1_code, admin2_code, admin1_code, population, elevation, timezone))

                    inserted += 1

                    # Commit em lotes
                    if inserted % 1000 == 0:
                        conn.commit()

                except Exception as e:
                    self.logger.debug(f"[GEONAMES] Erro linha {line_num}: {e}")
                    continue

        conn.commit()
        conn.close()

        self.logger.info(f"[GEONAMES] ✅ Carga concluída: {inserted:,} locais carregados ({skipped:,} ignorados)")

    def search_neighborhoods(self, city: str, state: str, limit: int = 50) -> List[Dict[str, any]]:
        """
        Busca bairros de uma cidade no cache offline
        Retorna lista de dicionários com name, latitude, longitude
        """
        if not self.CACHE_DB.exists():
            return []

        try:
            conn = sqlite3.connect(self.CACHE_DB)
            cursor = conn.cursor()

            # Buscar no cache municipalities_coordinates primeiro para pegar cidade exata
            cursor.execute("""
                SELECT city FROM municipalities_coordinates 
                WHERE UPPER(city) = UPPER(?) AND UPPER(state) = UPPER(?)
                LIMIT 1
            """, (city, state))

            city_match = cursor.fetchone()
            city_search = city_match[0] if city_match else city

            # Buscar bairros próximos à cidade
            cursor.execute("""
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
            """, (state, city_search, city_search, state, limit))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'name': row[0],
                    'latitude': row[1],
                    'longitude': row[2],
                    'feature_code': row[3],
                    'population': row[4]
                })

            conn.close()
            return results

        except Exception as e:
            self.logger.error(f"[GEONAMES] ❌ Erro ao buscar bairros: {e}")
            return []

    def get_city_coordinates(self, city: str, state: str) -> Optional[Tuple[float, float]]:
        """
        Retorna coordenadas (lat, lon) de uma cidade do cache
        Primeiro tenta municipalities_coordinates, depois cities_ibge, por fim GeoNames
        """
        if not self.CACHE_DB.exists():
            return None

        try:
            conn = sqlite3.connect(self.CACHE_DB)
            cursor = conn.cursor()

            # 1. Tentar municipalities_coordinates (mais rápido)
            cursor.execute("""
                SELECT latitude, longitude 
                FROM municipalities_coordinates
                WHERE UPPER(city) = UPPER(?) AND UPPER(state) = UPPER(?)
                LIMIT 1
            """, (city, state))

            result = cursor.fetchone()
            if result:
                conn.close()
                return (result[0], result[1])

            # 2. Tentar cities_ibge
            cursor.execute("""
                SELECT latitude, longitude
                FROM cities_ibge
                WHERE UPPER(name) = UPPER(?) AND UPPER(state_code) = UPPER(?)
                AND latitude IS NOT NULL AND longitude IS NOT NULL
                LIMIT 1
            """, (city, state))

            result = cursor.fetchone()
            if result:
                conn.close()
                return (result[0], result[1])

            # 3. Fallback: GeoNames (capitais ou cidades grandes)
            cursor.execute("""
                SELECT latitude, longitude
                FROM neighborhoods_geonames
                WHERE UPPER(name) = UPPER(?) AND state_code = ?
                AND feature_code IN ('PPLA', 'PPLA2', 'PPLA3', 'PPL')
                ORDER BY population DESC
                LIMIT 1
            """, (city, state))

            result = cursor.fetchone()
            conn.close()

            if result:
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
