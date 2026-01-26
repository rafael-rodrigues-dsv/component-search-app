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

    def __init__(self):
        self.config = ConfigManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PythonSearchApp/4.0.0 (Geographic Discovery)'
        })

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
        """Obter coordenadas via ViaCEP"""
        if not self.config.get_config_value('geographic_discovery.apis.viacep.enabled', True):
            return None
            
        try:
            url = self.config.get_config_value('geographic_discovery.apis.viacep.url')
            clean_cep = cep.replace('-', '').replace('.', '')
            
            response = self.session.get(f"{url}/{clean_cep}/json/", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'erro' in data:
                return None
            
            # Geocodificar cidade via Nominatim
            coords = self._geocode_city(data['localidade'], data['uf'])
            
            return {
                'cep': cep,
                'cidade': data['localidade'],
                'uf': data['uf'],
                'lat': coords[0] if coords else None,
                'lng': coords[1] if coords else None
            }
            
        except Exception as e:
            print(f"[GEO] Erro ViaCEP: {e}")
            return None

    def _discover_nearby_cities(self, base_info: Dict, radius_km: int) -> List[Dict]:
        """Descobrir cidades próximas via IBGE (QUALQUER CIDADE COMO BASE)"""
        if not self.config.get_config_value('geographic_discovery.apis.ibge.enabled', True):
            return []
            
        try:
            # 1. Obter municípios com população via IBGE
            municipalities_with_pop = self._get_state_municipalities_with_population(base_info['uf'])
            
            # 2. Obter configurações do perfil detectado
            profile = self._detect_profile_from_cep(self.config.reference_cep)
            min_population = self.config.get_config_value(f'geographic_discovery.profiles.{profile}.min_city_population', 500000)
            target_cities = self.config.get_config_value(f'geographic_discovery.profiles.{profile}.target_large_cities', 10)
            
            # 3. Filtrar por população ANTES de geocodificar (economia massiva)
            large_cities = [m for m in municipalities_with_pop if m.get('population', 0) >= min_population]
            
            # Tratamento quando API IBGE não encontra cidades com população mínima
            if len(large_cities) == 0:
                if min_population > 0:
                    print(f"[GEO] ⚠️  AVISO: Nenhuma cidade encontrada com população >= {min_population:,} habitantes")
                    print(f"[GEO] 📊 Total de municípios no estado: {len(municipalities_with_pop)}")
                    
                    # Mostrar as 5 maiores cidades encontradas
                    if municipalities_with_pop:
                        load_logger.info(f"[GEO] 🏙️  Maiores cidades encontradas:")
                        for i, city in enumerate(municipalities_with_pop[:5]):
                            pop = city.get('population', 0)
                            print(f"[GEO]    {i+1}. {city['nome']} - {pop:,} habitantes")
                    
                    # Usar fallback apenas se existirem municípios
                    if municipalities_with_pop:
                        print(f"[GEO] 🔄 Usando fallback: primeiras 10 cidades por população")
                        large_cities = municipalities_with_pop[:10]
                    else:
                        print(f"[GEO] ❌ ERRO: API do IBGE não retornou dados de municípios para {base_info['uf']}")
                        return []
                else:
                    large_cities = municipalities_with_pop[:30]
            
            if min_population > 0:
                print(f"[GEO] 📈 {len(municipalities_with_pop)} municípios total, {len(large_cities)} com população >= {min_population:,} hab")
            else:
                print(f"[GEO] 📈 {len(municipalities_with_pop)} municípios total, {len(large_cities)} selecionadas")
            
            # 3. Geocodificar cidades grandes (limitado apenas pelo raio)
            cities_in_radius = []
            
            for i, municipality in enumerate(large_cities[:50]):  # Máximo 50 cidades grandes
                
                city_name = municipality['nome']
                is_base_city = city_name.lower() == base_info['cidade'].lower()
                
                print(f"    [GEO] Processando {i+1}/{min(len(large_cities), 50)}: {city_name} ({municipality.get('population', 0):,} hab)")
                
                # Geocodificar cidade
                coords = self._geocode_city(city_name, base_info['uf'])
                if not coords:
                    continue
                
                # Calcular distância
                distance = self._calculate_distance(
                    base_info['lat'], base_info['lng'],
                    coords[0], coords[1]
                )
                
                # Cidade base sempre entra, outras só se no raio
                if is_base_city or distance <= radius_km:
                    status = "🎯 BASE" if is_base_city else f"{round(distance, 1)}km"
                    print(f"    [GEO] ✅ Incluída: {city_name} ({municipality.get('population', 0):,} hab) - {status}")
                    
                    cities_in_radius.append({
                        'name': city_name,
                        'state': base_info['uf'],
                        'distance_km': round(distance, 1),
                        'coordinates': coords,
                        'ibge_code': municipality['id'],
                        'population': municipality.get('population', 0),
                        'is_base_city': is_base_city
                    })
                else:
                    print(f"    [GEO] ❌ Excluída: {city_name} ({municipality.get('population', 0):,} hab) - {round(distance, 1)}km - fora do raio")
                
                # Rate limiting otimizado
                time.sleep(0.2)  # Reduzido de 1s para 200ms
            
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
        """Geocodificar cidade via Nominatim"""
        if not self.config.get_config_value('geographic_discovery.apis.nominatim.enabled', True):
            return None
            
        try:
            url = self.config.get_config_value('geographic_discovery.apis.nominatim.url')
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
                return (float(data[0]['lat']), float(data[0]['lon']))
            
            return None
            
        except Exception as e:
            print(f"[GEO] Erro Nominatim para {city}: {e}")
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
        """Obter bairros via API IBGE Distritos"""
        if not self.config.get_config_value('geographic_discovery.apis.ibge.enabled', True):
            return []
            
        try:
            # Buscar código IBGE da cidade
            city_code = self._get_city_ibge_code(city, state)
            if not city_code:
                print(f"        [GEO] Código IBGE não encontrado para {city}")
                return []
            
            print(f"        [GEO] Consultando distritos IBGE para {city} (código: {city_code})...")
            
            # Buscar distritos via API IBGE
            base_url = self.config.get_config_value('geographic_discovery.apis.ibge.url')
            url = f"{base_url}/municipios/{city_code}/distritos"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            districts = response.json()
            print(f"        [GEO] {len(districts)} distritos encontrados")
            
            neighborhoods = [district['nome'] for district in districts if 'nome' in district]
            return neighborhoods  # Sem limite de bairros
            
        except Exception as e:
            print(f"        [GEO] Erro API IBGE Distritos: {e}")
            return []
    
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
        """Calcular distância usando fórmula de Haversine"""
        if not all([lat1, lng1, lat2, lng2]):
            return float('inf')
            
        # Converter para radianos
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        
        # Fórmula de Haversine
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Raio da Terra em km
        r = 6371
        
        return c * r
    
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
