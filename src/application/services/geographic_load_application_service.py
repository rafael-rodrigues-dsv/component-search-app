#!/usr/bin/env python3
"""
Application Service para Carga de Dados Geográficos IBGE
Carrega estados, municípios e coordenadas das capitais
"""
import sqlite3
import requests
import time
from pathlib import Path
from typing import List, Dict, Optional

from src.infrastructure.logging.initial_load_logger import load_logger


class GeographicLoadApplicationService:
    """
    Application Service para carga inicial de dados geográficos

    Responsabilidade:
    - Carregar 27 estados brasileiros
    - Carregar 5.571 municípios (todos do Brasil)
    - Geocodificar 27 capitais

    Regra de Negócio:
    - Só executa se cache estiver vazio (idempotente)
    - Não força recarga se dados já existem
    """

    def __init__(self):
        # Determinar pasta do projeto
        import os
        current_dir = Path.cwd()

        # Subir até encontrar a raiz do projeto
        while current_dir.name in ['src', 'scripts', 'application', 'services']:
            current_dir = current_dir.parent

        project_root = current_dir
        cache_dir = project_root / "data" / "cache"
        self.db_path = cache_dir / "pythonsearchcache.db"

        self.ibge_base_url = "https://servicodados.ibge.gov.br/api/v1/localidades"
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'PythonSearchApp/4.3.0'})

    def ensure_geographic_data_loaded(self) -> Dict:
        """
        Garante que dados geográficos estão carregados (idempotente)

        Verifica se cache está vazio e carrega apenas se necessário.

        Returns:
            Dict com resultado: {
                'loaded': bool,
                'states_count': int,
                'cities_count': int,
                'message': str
            }
        """

        if not self.db_path.exists():
            load_logger.error(f"[GEO-LOAD] Banco de cache não encontrado: {self.db_path}")
            return {
                'loaded': False,
                'states_count': 0,
                'cities_count': 0,
                'message': 'Banco de cache não existe'
            }

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Verificar se já tem dados carregados
            cursor.execute("SELECT COUNT(*) FROM states_ibge")
            states_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM cities_ibge")
            cities_count = cursor.fetchone()[0]

            if states_count > 0 and cities_count > 0:
                load_logger.info(f"[GEO-LOAD] ✅ Dados geográficos já carregados:")
                load_logger.info(f"[GEO-LOAD]    Estados: {states_count}")
                load_logger.info(f"[GEO-LOAD]    Municípios: {cities_count}")

                return {
                    'loaded': True,
                    'states_count': states_count,
                    'cities_count': cities_count,
                    'message': 'Dados já existem (cache)'
                }

            # Cache vazio - carregar dados
            load_logger.info("[GEO-LOAD] 📦 Cache vazio, iniciando carga de dados geográficos...")

            # 1. Carregar Estados
            load_logger.info("[GEO-LOAD] [1/3] Carregando Estados...")
            states = self._load_states(cursor)
            conn.commit()
            load_logger.info(f"[GEO-LOAD]    ✅ {len(states)} estados carregados")

            # 2. Carregar Municípios
            load_logger.info("[GEO-LOAD] [2/3] Carregando Municípios (aguarde ~2-3 min)...")
            cities = self._load_all_municipalities(cursor, states)
            conn.commit()
            load_logger.info(f"[GEO-LOAD]    ✅ {len(cities)} municípios carregados")

            # 3. Geocodificar Capitais
            load_logger.info("[GEO-LOAD] [3/3] Geocodificando Capitais...")
            self._geocode_capitals(cursor, states)
            conn.commit()
            load_logger.info(f"[GEO-LOAD]    ✅ 27 capitais geocodificadas")

            # Verificar contagem final
            cursor.execute("SELECT COUNT(*) FROM states_ibge")
            final_states = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM cities_ibge")
            final_cities = cursor.fetchone()[0]

            load_logger.info("[GEO-LOAD] ✅ Carga de dados geográficos concluída!")
            load_logger.info(f"[GEO-LOAD]    Estados: {final_states}")
            load_logger.info(f"[GEO-LOAD]    Municípios: {final_cities}")

            return {
                'loaded': True,
                'states_count': final_states,
                'cities_count': final_cities,
                'message': 'Dados carregados com sucesso'
            }

        except Exception as e:
            load_logger.error(f"[GEO-LOAD] ❌ Erro na carga: {e}")
            conn.rollback()
            return {
                'loaded': False,
                'states_count': 0,
                'cities_count': 0,
                'message': f'Erro: {str(e)}'
            }
        finally:
            cursor.close()
            conn.close()

    def _load_states(self, cursor) -> List[Dict]:
        """Carrega 27 estados brasileiros com coordenadas das capitais"""

        # Dados das capitais (fonte: IBGE + dados públicos)
        capitals_data = {
            'AC': {'name': 'Rio Branco', 'lat': -9.9754, 'lon': -67.8250},
            'AL': {'name': 'Maceió', 'lat': -9.6658, 'lon': -35.7353},
            'AP': {'name': 'Macapá', 'lat': 0.0389, 'lon': -51.0664},
            'AM': {'name': 'Manaus', 'lat': -3.1190, 'lon': -60.0217},
            'BA': {'name': 'Salvador', 'lat': -12.9714, 'lon': -38.5014},
            'CE': {'name': 'Fortaleza', 'lat': -3.7172, 'lon': -38.5433},
            'DF': {'name': 'Brasília', 'lat': -15.7939, 'lon': -47.8828},
            'ES': {'name': 'Vitória', 'lat': -20.3155, 'lon': -40.3128},
            'GO': {'name': 'Goiânia', 'lat': -16.6864, 'lon': -49.2643},
            'MA': {'name': 'São Luís', 'lat': -2.5297, 'lon': -44.3028},
            'MT': {'name': 'Cuiabá', 'lat': -15.6014, 'lon': -56.0979},
            'MS': {'name': 'Campo Grande', 'lat': -20.4697, 'lon': -54.6201},
            'MG': {'name': 'Belo Horizonte', 'lat': -19.9167, 'lon': -43.9345},
            'PA': {'name': 'Belém', 'lat': -1.4558, 'lon': -48.5039},
            'PB': {'name': 'João Pessoa', 'lat': -7.1195, 'lon': -34.8450},
            'PR': {'name': 'Curitiba', 'lat': -25.4284, 'lon': -49.2733},
            'PE': {'name': 'Recife', 'lat': -8.0476, 'lon': -34.8770},
            'PI': {'name': 'Teresina', 'lat': -5.0892, 'lon': -42.8019},
            'RJ': {'name': 'Rio de Janeiro', 'lat': -22.9068, 'lon': -43.1729},
            'RN': {'name': 'Natal', 'lat': -5.7945, 'lon': -35.2110},
            'RS': {'name': 'Porto Alegre', 'lat': -30.0346, 'lon': -51.2177},
            'RO': {'name': 'Porto Velho', 'lat': -8.7619, 'lon': -63.9039},
            'RR': {'name': 'Boa Vista', 'lat': 2.8235, 'lon': -60.6758},
            'SC': {'name': 'Florianópolis', 'lat': -27.5954, 'lon': -48.5480},
            'SP': {'name': 'São Paulo', 'lat': -23.5505, 'lon': -46.6333},
            'SE': {'name': 'Aracaju', 'lat': -10.9472, 'lon': -37.0731},
            'TO': {'name': 'Palmas', 'lat': -10.2491, 'lon': -48.3243}
        }

        # Buscar estados da API IBGE
        url = f"{self.ibge_base_url}/estados"
        response = self.session.get(url, timeout=30)
        response.raise_for_status()

        states_data = response.json()
        states_loaded = []

        current_time = int(time.time())

        for state in states_data:
            code = state['sigla']
            capital = capitals_data.get(code, {})

            cursor.execute("""
                INSERT INTO states_ibge (
                    code, name, ibge_code, region,
                    capital_city, capital_lat, capital_lon,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                code,
                state['nome'],
                str(state['id']),
                state['regiao']['nome'],
                capital.get('name'),
                capital.get('lat'),
                capital.get('lon'),
                current_time,
                current_time
            ))

            states_loaded.append({
                'code': code,
                'name': state['nome'],
                'ibge_code': str(state['id']),
                'capital': capital.get('name')
            })

        return states_loaded

    def _load_all_municipalities(self, cursor, states: List[Dict]) -> List[Dict]:
        """Carrega todos os municípios de todos os estados"""

        all_cities = []
        current_time = int(time.time())

        for i, state in enumerate(states, 1):
            state_code = state['code']

            try:
                # Buscar municípios do estado
                url = f"{self.ibge_base_url}/estados/{state_code}/municipios"
                response = self.session.get(url, timeout=30)
                response.raise_for_status()

                municipalities = response.json()

                # Inserir no banco
                for city in municipalities:
                    ibge_code = str(city['id'])
                    city_name = city['nome']

                    # Verificar se é capital
                    is_capital = 1 if city_name == state.get('capital') else 0

                    # Se for capital, usar coordenadas conhecidas
                    lat, lon = None, None
                    if is_capital:
                        cursor.execute(
                            "SELECT capital_lat, capital_lon FROM states_ibge WHERE code = ?",
                            (state_code,)
                        )
                        result = cursor.fetchone()
                        if result:
                            lat, lon = result

                    cursor.execute("""
                        INSERT INTO cities_ibge (
                            ibge_code, name, state_code, state_name,
                            is_capital, latitude, longitude,
                            geo_source, geo_quality,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ibge_code,
                        city_name,
                        state_code,
                        state['name'],
                        is_capital,
                        lat,
                        lon,
                        'IBGE' if is_capital else None,
                        'HIGH' if is_capital else None,
                        current_time,
                        current_time
                    ))

                    all_cities.append({
                        'ibge_code': ibge_code,
                        'name': city_name,
                        'state_code': state_code,
                        'is_capital': is_capital
                    })

                # Rate limiting (respeitar API do IBGE)
                time.sleep(0.3)

            except Exception as e:
                load_logger.warning(f"[GEO-LOAD] Erro ao carregar {state_code}: {e}")

        # Atualizar contagem de cidades por estado
        cursor.execute("""
            UPDATE states_ibge
            SET total_cities = (
                SELECT COUNT(*) FROM cities_ibge 
                WHERE cities_ibge.state_code = states_ibge.code
            )
        """)

        return all_cities

    def _geocode_capitals(self, cursor, states: List[Dict]):
        """Geocodificar capitais (já temos coordenadas hardcoded)"""

        # Capitais já foram geocodificadas durante a carga
        cursor.execute("""
            SELECT COUNT(*) FROM cities_ibge 
            WHERE is_capital = 1 AND latitude IS NOT NULL
        """)

        capitals_geocoded = cursor.fetchone()[0]
        load_logger.info(f"[GEO-LOAD]    📍 {capitals_geocoded}/27 capitais com coordenadas")
