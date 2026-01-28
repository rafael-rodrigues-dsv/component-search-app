"""
Application Service - Descoberta de Bairros via Nominatim OSM
Responsável por descobrir bairros de cidades usando OpenStreetMap (gratuito)
"""
import time
from typing import List

import requests

from ...infrastructure.cache.neighborhoods_cache import NeighborhoodsCache
from ...infrastructure.config.config_manager import ConfigManager


class NeighborhoodDiscoveryApplicationService:
    """
    Serviço de aplicação para descobrir bairros de cidades
    Usa Nominatim OSM com cache persistente
    """

    def __init__(self):
        self.config = ConfigManager()
        self.cache = NeighborhoodsCache()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PythonSearchApp/4.0.0 (Neighborhood Discovery)'
        })
        self.nominatim_url = self.config.get_config_value(
            'geographic_discovery.apis.nominatim.url',
            'https://nominatim.openstreetmap.org'
        )

    def discover_neighborhoods(self, city: str, state: str, use_cache: bool = True) -> List[str]:
        """
        Descobre bairros de uma cidade usando Nominatim OSM

        Args:
            city: Nome da cidade
            state: Sigla do estado (ex: SP, RJ)
            use_cache: Se True, tenta buscar do cache primeiro

        Returns:
            Lista de nomes de bairros
        """
        if not city or not state:
            return []

        # 1. Tentar cache primeiro (se habilitado)
        if use_cache:
            cached = self.cache.get_neighborhoods(city, state)
            if cached is not None:
                print(f"        [BAIRROS] 📦 Cache: {len(cached)} bairros de {city}")
                return cached

        # 2. Buscar via Nominatim OSM
        print(f"        [BAIRROS] 🌐 Consultando Nominatim para {city}/{state}...")
        neighborhoods = self._fetch_from_nominatim(city, state)

        # 3. Filtrar e limpar resultados
        neighborhoods = self._filter_neighborhoods(neighborhoods, city)

        # 4. Salvar no cache
        if neighborhoods:
            self.cache.set_neighborhoods(city, state, neighborhoods, source='nominatim')
            print(f"        [BAIRROS] ✅ {len(neighborhoods)} bairros descobertos e cacheados")
        else:
            print(f"        [BAIRROS] ⚠️  Nenhum bairro encontrado via Nominatim")

        return neighborhoods

    def _fetch_from_nominatim(self, city: str, state: str) -> List[str]:
        """Busca bairros via Nominatim OSM"""
        neighborhoods = set()

        try:
            # Estratégia 1: Buscar por "neighbourhood" + cidade
            neighborhoods.update(
                self._query_nominatim(f"neighbourhood {city}, {state}, Brazil", limit=50)
            )

            # Estratégia 2: Buscar por "suburb" (também são bairros)
            neighborhoods.update(
                self._query_nominatim(f"suburb {city}, {state}, Brazil", limit=50)
            )

            # Rate limiting (Nominatim exige máximo 1 req/s)
            time.sleep(1.1)

        except Exception as e:
            print(f"        [BAIRROS] Erro Nominatim: {e}")

        return sorted(list(neighborhoods))

    def _query_nominatim(self, query: str, limit: int = 50) -> List[str]:
        """Faz query no Nominatim e retorna lista de nomes"""
        neighborhoods = []

        try:
            url = f"{self.nominatim_url}/search"
            params = {
                'q': query,
                'format': 'json',
                'limit': limit,
                'addressdetails': 1,
                'accept-language': 'pt-BR'
            }

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            for item in data:
                # Extrair nome do bairro de diferentes campos
                name = None

                # Tentar pegar de 'address'
                if 'address' in item:
                    addr = item['address']
                    name = (
                        addr.get('neighbourhood') or
                        addr.get('suburb') or
                        addr.get('quarter') or
                        addr.get('district')
                    )

                # Fallback: usar 'display_name' (primeira parte)
                if not name and 'display_name' in item:
                    parts = item['display_name'].split(',')
                    if parts:
                        name = parts[0].strip()

                if name:
                    neighborhoods.append(name)

            # Rate limiting entre requests
            time.sleep(1.1)

        except requests.RequestException as e:
            print(f"        [BAIRROS] Erro de rede Nominatim: {e}")
        except Exception as e:
            print(f"        [BAIRROS] Erro ao processar Nominatim: {e}")

        return neighborhoods

    def _filter_neighborhoods(self, neighborhoods: List[str], city_name: str) -> List[str]:
        """
        Filtra e limpa lista de bairros

        - Remove duplicatas
        - Remove bairros com nome da cidade (redundante)
        - Remove nomes muito curtos ou suspeitos
        """
        filtered = set()
        city_lower = city_name.lower().strip()

        for neighborhood in neighborhoods:
            if not neighborhood:
                continue

            name = neighborhood.strip()
            name_lower = name.lower()

            # Filtro 1: Não incluir se for o mesmo nome da cidade
            if name_lower == city_lower:
                continue

            # Filtro 2: Não incluir nomes muito curtos (< 3 caracteres)
            if len(name) < 3:
                continue

            # Filtro 3: Não incluir se for nome de estado
            states = ['sp', 'rj', 'mg', 'rs', 'pr', 'ba', 'ce', 'pe', 'sc', 'go', 'df']
            if name_lower in states:
                continue

            # Filtro 4: Não incluir "Brazil" ou "Brasil"
            if name_lower in ['brazil', 'brasil']:
                continue

            filtered.add(name)

        return sorted(list(filtered))

    def get_cache_stats(self) -> dict:
        """Retorna estatísticas do cache de bairros"""
        return self.cache.get_stats()

    def clear_old_cache(self, days: int = 90) -> int:
        """Remove cache antigo"""
        return self.cache.clear_old_entries(days)

    def force_refresh(self, city: str, state: str) -> List[str]:
        """Força atualização dos bairros (ignora cache)"""
        print(f"        [BAIRROS] 🔄 Forçando atualização de {city}/{state}...")
        return self.discover_neighborhoods(city, state, use_cache=False)
