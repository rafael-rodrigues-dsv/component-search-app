"""
Serviço de Descoberta Geográfica Dinâmica
Descobre cidades e bairros automaticamente baseado em CEP + raio
"""
import math
import time
from typing import Dict, List, Optional, Tuple

import requests

from ...infrastructure.config.config_manager import ConfigManager
from src.infrastructure.logging.initial_load_logger import load_logger


class DynamicGeographicDiscoveryService:
    """Serviço para descoberta dinâmica de localizações geográficas"""

    # Mapa de estados vizinhos do Brasil (fronteiras reais)
    NEIGHBORING_STATES = {
        'AC': ['AM', 'RO'],
        'AL': ['SE', 'PE', 'BA'],
        'AP': ['PA'],
        'AM': ['RR', 'PA', 'MT', 'RO', 'AC'],
        'BA': ['SE', 'AL', 'PE', 'PI', 'TO', 'GO', 'MG', 'ES'],
        'CE': ['RN', 'PB', 'PE', 'PI'],
        'DF': ['GO'],
        'ES': ['BA', 'MG', 'RJ'],
        'GO': ['TO', 'BA', 'MG', 'MS', 'MT', 'DF'],
        'MA': ['PI', 'TO', 'PA'],
        'MT': ['RO', 'AM', 'PA', 'TO', 'GO', 'MS'],
        'MS': ['MT', 'GO', 'MG', 'SP', 'PR'],
        'MG': ['BA', 'ES', 'RJ', 'SP', 'MS', 'GO'],
        'PA': ['AP', 'AM', 'RR', 'MT', 'TO', 'MA'],
        'PB': ['RN', 'CE', 'PE'],
        'PR': ['SP', 'MS', 'SC'],
        'PE': ['PB', 'CE', 'PI', 'BA', 'AL'],
        'PI': ['MA', 'TO', 'BA', 'PE', 'CE'],
        'RJ': ['ES', 'MG', 'SP'],
        'RN': ['CE', 'PB'],
        'RS': ['SC'],
        'RO': ['AC', 'AM', 'MT'],
        'RR': ['AM', 'PA'],
        'SC': ['PR', 'RS'],
        'SP': ['MG', 'RJ', 'PR', 'MS'],
        'SE': ['BA', 'AL'],
        'TO': ['MA', 'PI', 'BA', 'GO', 'MT', 'PA']
    }

    def __init__(self):
        self.config = ConfigManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PythonSearchApp/4.0.0 (Geographic Discovery)'
        })

        # Inicializar cache de coordenadas de cidades
        from ...infrastructure.cache.cities_coordinates_cache import CitiesCoordinatesCache
        self.cities_cache = CitiesCoordinatesCache()

        # Inicializar cache de distâncias
        from ...infrastructure.cache.distance_cache import DistanceCache
        self.distance_cache = DistanceCache()


        # Pré-carregar coordenadas das principais cidades (uma única vez)
        self._preload_major_cities_if_needed()

    def discover_locations_from_config(self) -> Dict:
        """Descobre localizações baseado na configuração YAML com perfil automático"""
        cep = self.config.reference_cep
        
        # Detectar perfil automaticamente baseado no CEP
        profile = self._detect_profile_from_cep(cep)
        profile_name = "metropolitana" if profile == "metropolitan" else "rural"
        
        # Prefer RAIO_KM from TB_CEP_CONFIG if present (user-configurable); otherwise use YAML profile
        try:
            from src.application.services.zip_code_application_service import ZipCodeApplicationService
            zip_svc = ZipCodeApplicationService()
            cep_row = zip_svc.get_reference_cep() or {}
            radius_km = cep_row.get('raio_km') if isinstance(cep_row, dict) and cep_row.get('raio_km') is not None else None
        except Exception:
            radius_km = None
        if radius_km is None:
            radius_km = self.config.get_config_value(f'geographic_discovery.profiles.{profile}.radius_km', 50)

        print(f"[GEO] 🚀 Descobrindo região ao redor do CEP {cep}")
        print(f"[GEO] 🏙️ Perfil detectado: {profile_name.upper()}")
        print(f"[GEO] 📍 Raio de busca: {radius_km}km")
        
        # 1. Obter coordenadas do CEP base
        base_info = self._get_cep_coordinates(cep)
        if not base_info:
            raise Exception(f"CEP {cep} não encontrado")
        
        print(f"[GEO] 🎯 Base: {base_info['cidade']}/{base_info['uf']} ({base_info['lat']}, {base_info['lng']})")
        
        # 2. Descobrir cidades próximas (qualquer cidade como centro)
        cities = self._discover_nearby_cities(base_info, radius_km)
        print(f"[GEO] 🏙️ {len(cities)} cidades encontradas")
        
        # 3. Descobrir bairros da cidade base + cidades próximas
        neighborhoods = self._discover_neighborhoods_nearby(cities, base_info)
        print(f"[GEO] 🏘️ {len(neighborhoods)} bairros descobertos (sem limite)")
        
        # Salvar cidades e bairros descobertos no banco
        self._save_discovered_locations_to_db(cities, neighborhoods, base_info['uf'])
        
        return {
            'base_city': base_info['cidade'],
            'base_state': base_info['uf'],
            'base_coordinates': (base_info['lat'], base_info['lng']),
            'cities': cities,
            'neighborhoods': neighborhoods,
            'total_locations': len(cities) + len(neighborhoods)
        }

    def _get_cep_coordinates(self, cep: str) -> Optional[Dict]:
        """Obter coordenadas via BrasilAPI com cache"""
        if not self.config.get_config_value('geographic_discovery.apis.brasilapi.enabled', True):
            return None
            
        try:
            # Usar CepResolverService (BrasilAPI + Cache)
            from ...infrastructure.services.cep_resolver_service import CepResolverService
            cep_service = CepResolverService()

            data = cep_service.get_cep_data(cep)
            if not data:
                return None
            
            # Geocodificar cidade via Nominatim/Cache
            coords = self._geocode_city(data['localidade'], data['uf'])
            
            return {
                'cep': cep,
                'cidade': data['localidade'],
                'uf': data['uf'],
                'lat': coords[0] if coords else None,
                'lng': coords[1] if coords else None
            }
            
        except Exception as e:
            print(f"[GEO] Erro BrasilAPI: {e}")
            return None

    def _discover_nearby_cities(self, base_info: Dict, radius_km: int) -> List[Dict]:
        """Descobrir cidades próximas - BUSCA MULTI-ESTADO INTELIGENTE baseada no raio"""
        if not self.config.get_config_value('geographic_discovery.apis.ibge.enabled', True):
            return []
            
        try:
            # 1. Determinar quais estados buscar baseado no raio
            states_to_search = self._get_states_to_search(base_info['uf'], radius_km)

            print(f"[GEO] 🇧🇷 Raio de {radius_km}km → Buscando em {len(states_to_search)} estado(s): {', '.join(states_to_search)}")

            # 2. Buscar municípios dos estados relevantes
            municipalities_with_pop = []
            for uf in states_to_search:
                uf_cities = self._get_state_municipalities_with_population(uf)
                municipalities_with_pop.extend(uf_cities)
                print(f"[GEO]    ✅ {uf}: {len(uf_cities)} municípios obtidos")

            # 3. Obter configurações do perfil detectado
            profile = self._detect_profile_from_cep(self.config.reference_cep)
            min_population = self.config.get_config_value(f'geographic_discovery.profiles.{profile}.min_city_population', 500000)
            target_cities = self.config.get_config_value(f'geographic_discovery.profiles.{profile}.target_large_cities', 10)
            
            # 4. Filtrar por população ANTES de geocodificar (economia massiva)
            large_cities = [m for m in municipalities_with_pop if m.get('population', 0) >= min_population]
            
            # Tratamento quando API IBGE não encontra cidades com população mínima
            if len(large_cities) == 0:
                if min_population > 0:
                    print(f"[GEO] ⚠️  AVISO: Nenhuma cidade encontrada com população >= {min_population:,} habitantes")
                    print(f"[GEO] 📊 Total de municípios nos estados: {len(municipalities_with_pop)}")

                    # Mostrar as 5 maiores cidades encontradas
                    if municipalities_with_pop:
                        municipalities_with_pop_sorted = sorted(municipalities_with_pop, key=lambda x: x.get('population', 0), reverse=True)
                        print(f"[GEO] 🏙️  Maiores cidades encontradas:")
                        for i, city in enumerate(municipalities_with_pop_sorted[:5]):
                            pop = city.get('population', 0)
                            city_uf = city.get('uf', 'N/A')
                            print(f"[GEO]    {i+1}. {city['nome']}/{city_uf} - {pop:,} habitantes")

                        # Usar fallback apenas se existirem municípios
                        print(f"[GEO] 🔄 Usando fallback: primeiras 10 cidades por população")
                        large_cities = municipalities_with_pop_sorted[:10]
                    else:
                        print(f"[GEO] ❌ ERRO: API do IBGE não retornou dados de municípios")
                        return []
                else:
                    large_cities = municipalities_with_pop[:30]
            
            if min_population > 0:
                print(f"[GEO] 📈 {len(municipalities_with_pop)} municípios total, {len(large_cities)} com população >= {min_population:,} hab")
            else:
                print(f"[GEO] 📈 {len(municipalities_with_pop)} municípios total, {len(large_cities)} selecionadas")
            
            # 5. Distribuir cidades de forma equilibrada entre os estados
            # Pegar até 50 cidades por estado (prioritizando as maiores de cada estado)
            cities_to_process = []
            cities_by_state = {}

            # Agrupar cidades por estado
            for city in large_cities:
                uf = city.get('uf', base_info['uf'])
                if uf not in cities_by_state:
                    cities_by_state[uf] = []
                cities_by_state[uf].append(city)

            # Pegar até 50 cidades de cada estado (já ordenadas por população)
            max_per_state = 50
            for uf in sorted(cities_by_state.keys()):
                cities_to_process.extend(cities_by_state[uf][:max_per_state])

            total_cities = len(cities_to_process)

            # 6. Geocodificar cidades selecionadas (OTIMIZADO: cache em batch mas logs completos)
            cities_in_radius = []

            print(f"[GEO] 🔄 Iniciando processamento de {total_cities} cidades...")

            # OTIMIZAÇÃO: Verificar cache e geocodificar em tempo real com logs
            cities_with_coords = []

            for i, municipality in enumerate(cities_to_process):
                city_name = municipality['nome']
                city_uf = municipality.get('uf', base_info['uf'])

                # LOG IMEDIATO: Processando cidade
                print(f"    [GEO] Processando {i+1}/{total_cities}: {city_name}/{city_uf} ({municipality.get('population', 0):,} hab)")

                # Tentar cache primeiro (instantâneo)
                coords = self.cities_cache.get_city_coordinates(city_name, city_uf)
                coords_from_cache = bool(coords)

                # Se não tem cache, geocodificar agora
                if not coords:
                    coords = self._geocode_city(city_name, city_uf)
                    if coords:
                        coords_from_cache = False
                        time.sleep(0.1)  # Rate limiting reduzido - Photon é mais rápido

                # Se conseguiu coordenadas (cache ou geocodificação), adicionar
                if coords:
                    cities_with_coords.append({
                        'municipality': municipality,
                        'coords': coords,
                        'from_cache': coords_from_cache
                    })

                    # Calcular distância IMEDIATAMENTE e mostrar resultado
                    is_base_city = city_name.lower() == base_info['cidade'].lower()

                    distance = self._calculate_distance(
                        base_info['lat'], base_info['lng'],
                        coords[0], coords[1]
                    )

                    # Determinar origem das coordenadas
                    source = "📦 CACHE" if coords_from_cache else "🌐 PHOTON"

                    # Cidade base sempre entra, outras só se no raio
                    if is_base_city or distance <= radius_km:
                        status = "🎯 BASE" if is_base_city else f"{round(distance, 1)}km"
                        print(f"    [GEO] ✅ Incluída: {city_name}/{city_uf} ({municipality.get('population', 0):,} hab) - {status} [{source}]")

                        cities_in_radius.append({
                            'name': city_name,
                            'state': city_uf,
                            'distance_km': round(distance, 1),
                            'coordinates': coords,
                            'ibge_code': municipality['id'],
                            'population': municipality.get('population', 0),
                            'is_base_city': is_base_city
                        })
                    else:
                        print(f"    [GEO] ❌ Excluída: {city_name}/{city_uf} ({municipality.get('population', 0):,} hab) - {round(distance, 1)}km - fora do raio [{source}]")

            print(f"[GEO] 🏙️ {len(cities_in_radius)} cidades encontradas")

            # Ordenar por distância (cidade base primeiro)
            cities_in_radius.sort(key=lambda x: (not x.get('is_base_city', False), x['distance_km']))

            return cities_in_radius
            
        except Exception as e:
            print(f"[GEO] Erro descoberta de cidades: {e}")
            return []

    def _get_state_municipalities(self, uf: str) -> List[Dict]:
        """Obter municípios do estado via IBGE (sem população)"""
        try:
            url = self.config.get_config_value('geographic_discovery.apis.ibge.url')
            full_url = f"{url}/estados/{uf}/municipios"
            
            load_logger.info(f"[GEO] 🌐 Consultando API IBGE: {full_url}")
            response = self.session.get(full_url, timeout=15)
            response.raise_for_status()
            
            municipalities = response.json()
            if not municipalities:
                print(f"[GEO] ⚠️  API IBGE retornou lista vazia para {uf}")
                return []
            
            print(f"[GEO] ✅ API IBGE: {len(municipalities)} municípios encontrados para {uf}")
            return municipalities
            
        except requests.exceptions.Timeout:
            print(f"[GEO] ⏰ TIMEOUT: API IBGE não respondeu em 15s para {uf}")
            return []
        except requests.exceptions.ConnectionError:
            print(f"[GEO] 🌐 ERRO DE CONEXÃO: Não foi possível conectar à API IBGE")
            return []
        except requests.exceptions.HTTPError as e:
            print(f"[GEO] 🚫 ERRO HTTP {e.response.status_code}: {e}")
            return []
        except Exception as e:
            print(f"[GEO] ❌ ERRO INESPERADO na API IBGE: {e}")
            return []
    

    
    def _add_population_to_cities(self, cities: List[Dict], region_name: str) -> List[Dict]:
        """Adicionar população a lista de cidades (sem parada otimizada)"""
        print(f"[GEO] 📊 Consultando população de {len(cities)} cidades da região {region_name}...")
        
        cities_with_pop = []
        # Detectar perfil e usar configurações correspondentes
        profile = self._detect_profile_from_cep(self.config.reference_cep)
        min_population = self.config.get_config_value(f'geographic_discovery.profiles.{profile}.min_city_population', 500000)
        
        for i, city in enumerate(cities, 1):
            try:
                print(f"[GEO] 🔄 {i}/{len(cities)}: {city['nome']}")
                
                pop_url = f"https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/2022/variaveis/9324?localidades=N6[{city['id']}]"
                pop_response = self.session.get(pop_url, timeout=5)
                
                population = 0
                if pop_response.status_code == 200:
                    pop_data = pop_response.json()
                    if pop_data and len(pop_data) > 0:
                        resultados = pop_data[0].get('resultados', [])
                        if resultados and len(resultados) > 0:
                            series = resultados[0].get('series', [])
                            if series and len(series) > 0:
                                valores = series[0].get('serie', {})
                                if '2022' in valores:
                                    population = int(valores['2022'])
                
                city['population'] = population
                cities_with_pop.append(city)
                
                if population >= min_population:
                    print(f"[GEO] 🏙️  GRANDE: {city['nome']} - {population:,} hab")
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[GEO] ⚠️  Erro {city['nome']}: {e}")
                city['population'] = 0
                cities_with_pop.append(city)
        
        # Ordenar por população
        cities_with_pop.sort(key=lambda x: x.get('population', 0), reverse=True)
        
        large_cities = [c for c in cities_with_pop if c.get('population', 0) >= min_population]
        print(f"[GEO] ✅ Região {region_name}: {len(large_cities)} cidades grandes encontradas")
        
        return cities_with_pop
    
    def _add_population_to_cities_optimized(self, cities: List[Dict], target_cities: int, min_population: int) -> List[Dict]:
        """Adicionar população com parada otimizada (para todos os municípios)"""
        print(f"[GEO] 📊 Processando {len(cities)} municípios (parada otimizada em {target_cities} cidades grandes)...")
        
        cities_with_pop = []
        cities_found = 0
        
        for i, city in enumerate(cities, 1):
            try:
                if i <= 10 or i % 50 == 0 or i == len(cities):
                    print(f"[GEO] 🔄 Progresso: {i}/{len(cities)} - {city['nome']}")
                
                pop_url = f"https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/2022/variaveis/9324?localidades=N6[{city['id']}]"
                pop_response = self.session.get(pop_url, timeout=5)
                
                population = 0
                if pop_response.status_code == 200:
                    pop_data = pop_response.json()
                    if pop_data and len(pop_data) > 0:
                        resultados = pop_data[0].get('resultados', [])
                        if resultados and len(resultados) > 0:
                            series = resultados[0].get('series', [])
                            if series and len(series) > 0:
                                valores = series[0].get('serie', {})
                                if '2022' in valores:
                                    population = int(valores['2022'])
                
                city['population'] = population
                cities_with_pop.append(city)
                
                if population >= min_population:
                    cities_found += 1
                    print(f"[GEO] 🏙️  GRANDE #{cities_found}: {city['nome']} - {population:,} hab")
                    
                    if cities_found >= target_cities:
                        print(f"[GEO] ✅ Meta atingida: {cities_found} cidades grandes - parando busca")
                        # Adicionar cidades restantes sem população
                        for remaining in cities[i:]:
                            remaining['population'] = 0
                            cities_with_pop.append(remaining)
                        break
                
                time.sleep(0.1)
                
            except Exception as e:
                if i <= 10:
                    print(f"[GEO] ⚠️  Erro {city['nome']}: {e}")
                city['population'] = 0
                cities_with_pop.append(city)
        
        # Ordenar por população
        cities_with_pop.sort(key=lambda x: x.get('population', 0), reverse=True)
        
        large_cities = [c for c in cities_with_pop if c.get('population', 0) > 0]
        print(f"[GEO] ✅ Processamento concluído: {len(large_cities)} cidades com dados de população")
        
        return cities_with_pop
    
    def _get_state_municipalities_with_population(self, uf: str) -> List[Dict]:
        """Obter municípios via IBGE Cidades (SUPER RÁPIDO - 1 request)"""
        try:
            print(f"[GEO] 🚀 IBGE CIDADES - Buscando todas as cidades de {uf}...")
            
            # IBGE Cidades - dados completos em 1 request
            ibge_url = self.config.get_config_value('geographic_discovery.apis.ibge.url', 'https://servicodados.ibge.gov.br/api/v1/localidades')
            url = f"{ibge_url}/estados/{uf}/municipios"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            cities = response.json()
            print(f"[GEO] ✅ IBGE: {len(cities)} cidades obtidas")
            
            # Adicionar população estimada baseada em capitais conhecidas
            formatted_cities = []
            for city in cities:
                population = self._estimate_city_population(city['nome'], uf)
                
                formatted_cities.append({
                    'id': city['id'],
                    'nome': city['nome'],
                    'uf': uf,  # Adicionar UF para suportar busca multi-estado
                    'population': population
                })
            
            # Ordenar por população (maiores primeiro)
            formatted_cities.sort(key=lambda x: x['population'], reverse=True)
            
            # Usar perfil detectado para população mínima
            profile = self._detect_profile_from_cep(self.config.reference_cep)
            min_population = self.config.get_config_value(f'geographic_discovery.profiles.{profile}.min_city_population', 500000)
            large_cities = [c for c in formatted_cities if c['population'] >= min_population]
            
            if not large_cities:
                load_logger.warning(f"[GEO] ⚠️  Nenhuma cidade >= {min_population:,} hab - usando top 15")
                large_cities = formatted_cities[:15]
            
            print(f"[GEO] 📊 {len(large_cities)} cidades grandes selecionadas")
            return large_cities
            
        except Exception as e:
            print(f"[GEO] ❌ ERRO IBGE: {e}")
            return []

    def _geocode_city(self, city: str, state: str) -> Optional[Tuple[float, float]]:
        """Geocodificar cidade via Cache → Photon/Nominatim (otimizado)"""
        # 1. TENTAR CACHE PRIMEIRO (instantâneo)
        cached_coords = self.cities_cache.get_city_coordinates(city, state)
        if cached_coords:
            return cached_coords

        # 2. TENTAR PHOTON PRIMEIRO (3-5x mais rápido que Nominatim)
        if self.config.get_config_value('geographic_discovery.apis.photon.enabled', False):
            coords = self._geocode_city_photon(city, state)
            if coords:
                return coords

        # 3. FALLBACK: NOMINATIM (se Photon falhar ou estiver desabilitado)
        if self.config.get_config_value('geographic_discovery.apis.nominatim.enabled', True):
            coords = self._geocode_city_nominatim(city, state)
            if coords:
                return coords

        return None

    def _geocode_city_photon(self, city: str, state: str) -> Optional[Tuple[float, float]]:
        """Geocodificar cidade via Photon (OpenStreetMap - mais rápido)"""
        try:
            url = self.config.get_config_value('geographic_discovery.apis.photon.url', 'https://photon.komoot.io')
            params = {
                'q': f"{city}, {state}, Brazil",
                'limit': 1
            }

            response = self.session.get(f"{url}/api", params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data and 'features' in data and len(data['features']) > 0:
                feature = data['features'][0]
                coords = feature['geometry']['coordinates']
                lon, lat = coords[0], coords[1]  # Photon retorna [lon, lat]

                # Salvar no cache para próximas vezes
                self.cities_cache.set_city_coordinates(city, state, lat, lon)

                return (lat, lon)

            return None

        except Exception as e:
            print(f"[GEO] ⚠️  Photon falhou para {city}/{state}: {e}")
            return None

    def _geocode_city_nominatim(self, city: str, state: str) -> Optional[Tuple[float, float]]:
        """Geocodificar cidade via Nominatim (fallback)"""
        try:
            url = self.config.get_config_value('geographic_discovery.apis.nominatim.url', 'https://nominatim.openstreetmap.org')
            params = {
                'q': f"{city}, {state}, Brazil",
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            
            response = self.session.get(f"{url}/search", params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data:
                lat, lon = float(data[0]['lat']), float(data[0]['lon'])

                # Salvar no cache para próximas vezes
                self.cities_cache.set_city_coordinates(city, state, lat, lon)

                return (lat, lon)

            return None
            
        except Exception as e:
            print(f"[GEO] ⚠️  Nominatim falhou para {city}/{state}: {e}")
            return None

    def _discover_neighborhoods_nearby(self, cities: List[Dict], base_info: Dict) -> List[Dict]:
        """Descobrir TODOS os bairros das cidades (sem filtro de raio)"""
        neighborhoods = []
        
        # Buscar bairros de TODAS as cidades descobertas
        for city in cities:
            print(f"    [GEO] Buscando bairros de {city['name']}")
            city_neighborhoods = self._get_city_neighborhoods(city['name'], base_info['uf'])
            
            # Processar TODOS os bairros (sem filtro de distância)
            neighborhood_results = self._process_all_neighborhoods(
                city_neighborhoods, city, base_info
            )
            neighborhoods.extend(neighborhood_results)
        
        return neighborhoods
    
    def _process_all_neighborhoods(self, neighborhoods_list: List[str], city: Dict, base_info: Dict) -> List[Dict]:
        """Processar TODOS os bairros sem filtro de distância"""
        if not neighborhoods_list:
            return []
        
        print(f"        [GEO] ⚡ Processando TODOS os {len(neighborhoods_list)} bairros (sem filtro)...")
        
        results = []
        city_distance = city['distance_km']
        
        for neighborhood in neighborhoods_list:
            # Incluir TODOS os bairros sem filtro de distância
            print(f"        [GEO] ✅ Incluído: {neighborhood} (cidade: {city['name']})")
            results.append({
                'name': neighborhood,
                'city': city['name'],
                'state': base_info['uf'],
                'distance_km': city_distance  # Usar distância da cidade
            })
        
        print(f"        [GEO] ✅ Processamento concluído: {len(results)} bairros incluídos")
        return results

    def _get_city_neighborhoods(self, city: str, state: str) -> List[str]:
        """
        Obter bairros com estratégia inteligente:
        - Se IBGE retornar 2+ distritos: usar apenas IBGE
        - Se IBGE retornar 0 ou 1 distrito: buscar no Nominatim (com cache)
        """
        if not self.config.get_config_value('geographic_discovery.apis.ibge.enabled', True):
            return []

        # ESTRATÉGIA 1: Tentar API IBGE primeiro
        try:
            city_code = self._get_city_ibge_code(city, state)
            if city_code:
                print(f"        [GEO] Consultando distritos IBGE para {city} (código: {city_code})...")

                base_url = self.config.get_config_value('geographic_discovery.apis.ibge.url')
                url = f"{base_url}/municipios/{city_code}/distritos"
                response = self.session.get(url, timeout=15)
                response.raise_for_status()

                districts = response.json()
                print(f"        [GEO] {len(districts)} distritos IBGE encontrados")

                # Filtrar bairros redundantes (mesmo nome da cidade)
                neighborhoods = []
                for district in districts:
                    if 'nome' in district:
                        district_name = district['nome'].strip()
                        if district_name.lower() != city.lower():
                            neighborhoods.append(district_name)

                # DECISÃO: Se encontrou 2+ bairros válidos no IBGE, usar apenas IBGE
                if len(neighborhoods) >= 2:
                    print(f"        [GEO] ✅ {len(neighborhoods)} bairros IBGE - usando apenas IBGE")
                    return neighborhoods

                # Se tem 0 ou 1 bairro, tentar Nominatim
                print(f"        [GEO] ⚠️  IBGE retornou apenas {len(neighborhoods)} bairro(s), buscando Nominatim...")

        except Exception as e:
            print(f"        [GEO] Erro API IBGE: {e}")

        # ESTRATÉGIA 2: Nominatim (quando IBGE tem poucos resultados)
        try:
            from ...application.services.neighborhood_discovery_application_service import NeighborhoodDiscoveryApplicationService

            neighborhood_service = NeighborhoodDiscoveryApplicationService()
            neighborhoods = neighborhood_service.discover_neighborhoods(city, state, use_cache=True)

            if neighborhoods:
                return neighborhoods

        except Exception as e:
            print(f"        [GEO] Erro Nominatim: {e}")

        # FALLBACK: Usar o nome da cidade como bairro
        print(f"        [GEO] ℹ️  Nenhum bairro encontrado, usando nome da cidade: {city}")
        return [city]


    def _get_city_ibge_code(self, city: str, state: str) -> Optional[str]:
        """Obter código IBGE da cidade"""
        try:
            url = f"{self.config.get_config_value('geographic_discovery.apis.ibge.url')}/estados/{state}/municipios"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            municipalities = response.json()
            
            # Buscar cidade (case insensitive)
            city_lower = city.lower()
            for municipality in municipalities:
                if municipality['nome'].lower() == city_lower:
                    return str(municipality['id'])
            
            return None
            
        except Exception as e:
            print(f"        [GEO] Erro ao buscar código IBGE: {e}")
            return None


    def _estimate_city_population(self, city_name: str, uf: str) -> int:
        """Estimar população baseada em capitais e cidades conhecidas"""
        city_lower = city_name.lower()
        
        # Capitais e grandes cidades por estado
        known_cities = {
            'SP': {
                'são paulo': 12400000, 'guarulhos': 1400000, 'campinas': 1200000,
                'são bernardo do campo': 850000, 'santo andré': 720000, 'osasco': 700000,
                'são josé dos campos': 720000, 'ribeirão preto': 700000, 'sorocaba': 680000
            },
            'RJ': {
                'rio de janeiro': 6775000, 'niterói': 515000, 'nova iguaçu': 820000,
                'duque de caxias': 920000, 'são gonçalo': 1080000
            },
            'MG': {
                'belo horizonte': 2530000, 'contagem': 660000, 'uberlândia': 700000,
                'juiz de fora': 570000
            },
            'RS': {
                'porto alegre': 1488000, 'caxias do sul': 520000, 'canoas': 350000
            },
            'PR': {
                'curitiba': 1963000, 'londrina': 580000, 'maringá': 430000
            },
            'BA': {
                'salvador': 2900000, 'feira de santana': 630000, 'vitória da conquista': 350000
            },
            'PE': {
                'recife': 1650000, 'jaboatão dos guararapes': 700000, 'olinda': 390000
            },
            'CE': {
                'fortaleza': 2700000, 'caucaia': 370000, 'juazeiro do norte': 280000
            }
        }
        
        # Verificar se é cidade conhecida
        if uf in known_cities and city_lower in known_cities[uf]:
            return known_cities[uf][city_lower]
        
        # Estimativa baseada em padrões
        if 'grande' in city_lower or 'metropolitana' in city_lower:
            return 800000
        elif any(word in city_lower for word in ['são', 'santo', 'santa']):
            return 300000  # Cidades com santos tendem a ser maiores
        elif len(city_name) <= 6:
            return 200000  # Nomes curtos tendem a ser cidades antigas/grandes
        else:
            return 80000   # Cidades menores

    def _save_discovered_locations_to_db(self, cities: List[Dict], neighborhoods: List[Dict], uf: str):
        """Salva cidades e bairros descobertos no banco de dados"""
        try:
            from src.domain.services.cities_domain_service import CitiesDomainService
            service = CitiesDomainService()

            print(f"[GEO] 💾 Salvando {len(cities)} cidades e {len(neighborhoods)} bairros no banco...")

            result = service.save_discovered(cities, neighborhoods, uf)

            print(f"[GEO] ✅ Localizações salvas: {result.get('cities', 0)} cidades, {result.get('neighborhoods', 0)} bairros")

        except Exception as e:
            print(f"[GEO] ⚠️ Erro ao salvar no banco: {e}")
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calcular distância usando fórmula de Haversine com cache"""
        if not all([lat1, lng1, lat2, lng2]):
            return float('inf')

        # 1. Verificar cache primeiro (instantâneo)
        cached_distance = self.distance_cache.get(lat1, lng1, lat2, lng2)
        if cached_distance is not None:
            return cached_distance

        # 2. Calcular distância (Haversine)
        # Converter para radianos
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        
        # Fórmula de Haversine
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Raio da Terra em km
        r = 6371
        distance_km = c * r

        # 3. Salvar no cache para próximas consultas
        self.distance_cache.set(
            math.degrees(lat1), math.degrees(lng1),
            math.degrees(lat2), math.degrees(lng2),
            distance_km
        )

        return distance_km

    def _detect_profile_from_cep(self, cep: str) -> str:
        """Detecta perfil (metropolitan/rural) baseado no CEP"""
        if not self.config.get_config_value('geographic_discovery.auto_profile_detection.enabled', True):
            return 'rural'  # Padrão se detecção desabilitada
        
        # Limpar CEP e obter primeiros 2 dígitos
        cep_clean = cep.replace('-', '').replace('.', '')
        if len(cep_clean) < 2:
            return 'rural'
        
        cep_prefix = cep_clean[:2]
        
        # Obter lista de prefixos metropolitanos
        metro_prefixes = self.config.get_config_value('geographic_discovery.auto_profile_detection.metropolitan_cep_prefixes', [])
        
        if cep_prefix in metro_prefixes:
            print(f"[GEO] 🏙️ CEP {cep} detectado como REGIÃO METROPOLITANA (prefixo {cep_prefix})")
            return 'metropolitan'
        else:
            print(f"[GEO] 🌾 CEP {cep} detectado como REGIÃO RURAL/INTERIOR (prefixo {cep_prefix})")
            return 'rural'

    def _preload_major_cities_if_needed(self):
        """Pré-carrega coordenadas das principais cidades brasileiras (uma vez)"""
        stats = self.cities_cache.get_cache_stats()

        # Se já tem pelo menos 50 cidades com coordenadas, não precisa pré-carregar
        if stats.get('with_coords', 0) >= 50:
            return

        print("[GEO] 📥 Pré-carregando coordenadas das principais cidades...")

        # Coordenadas das 100 maiores cidades do Brasil
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

        for (city, state), (lat, lon) in major_cities.items():
            self.cities_cache.set_city_coordinates(city, state, lat, lon)

        print(f"[GEO] ✅ {len(major_cities)} cidades pré-carregadas com sucesso")

    def _get_states_to_search(self, base_uf: str, radius_km: int) -> List[str]:
        """Determina quais estados buscar baseado no raio configurado

        Regras:
        - < 100km: Apenas o estado do CEP
        - 100-500km: Estado do CEP + vizinhos diretos
        - > 500km: Estado do CEP + vizinhos + vizinhos dos vizinhos

        Args:
            base_uf: UF do estado base (do CEP)
            radius_km: Raio de busca em km

        Returns:
            Lista de UFs a serem buscadas
        """
        states_to_search = [base_uf]  # Sempre incluir o estado base

        if radius_km < 100:
            # Raio pequeno: apenas o estado do CEP
            return states_to_search

        # Adicionar vizinhos diretos para raio >= 100km
        neighbors = self.NEIGHBORING_STATES.get(base_uf, [])
        states_to_search.extend(neighbors)

        # IMPORTANTE: Só adicionar vizinhos dos vizinhos se raio > 500km
        if radius_km > 500:
            # Raio muito grande (> 500km): adicionar vizinhos dos vizinhos
            second_level_neighbors = []
            for neighbor in neighbors:
                second_level = self.NEIGHBORING_STATES.get(neighbor, [])
                for state in second_level:
                    if state not in states_to_search and state not in second_level_neighbors:
                        second_level_neighbors.append(state)
            states_to_search.extend(second_level_neighbors)

        # Remover duplicatas e ordenar
        states_to_search = sorted(list(set(states_to_search)))

        return states_to_search

