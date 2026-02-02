"""
Application Service - Descoberta de Bairros via GeoNames (100% Offline)
Responsável por descobrir bairros de cidades usando dados GeoNames pré-carregados
"""
from typing import List, Dict
import logging

from ...infrastructure.cache.neighborhoods_cache import NeighborhoodsCache
from ...infrastructure.services.geonames_service import GeoNamesService


class NeighborhoodDiscoveryApplicationService:
    """
    Serviço de aplicação para descobrir bairros de cidades
    Usa GeoNames offline (100% após carga inicial)
    """

    def __init__(self):
        self.cache = NeighborhoodsCache()
        self.geonames = GeoNamesService()
        self.logger = logging.getLogger(__name__)
        self._ensure_geonames_loaded()

    def _ensure_geonames_loaded(self):
        """Garante que dados GeoNames estão carregados"""
        if not self.cache.is_geonames_loaded():
            self.logger.warning("[BAIRROS] ⚠️  Dados GeoNames não carregados. Iniciando carga...")
            print("[BAIRROS] 🌎 Primeira execução: carregando dados GeoNames...")
            print("[BAIRROS] ⏳ Isso pode levar 2-5 minutos na primeira vez...")
            
            success = self.geonames.download_and_load()
            
            if success:
                print("[BAIRROS] ✅ Dados GeoNames carregados com sucesso!")
                self.logger.info("[BAIRROS] ✅ GeoNames carregado e pronto para uso offline")
            else:
                print("[BAIRROS] ❌ Falha ao carregar GeoNames. Bairros podem estar limitados.")
                self.logger.error("[BAIRROS] ❌ Falha ao carregar GeoNames")

    def discover_neighborhoods(self, city: str, state: str, use_cache: bool = True) -> List[str]:
        """
        Descobre bairros de uma cidade usando GeoNames (100% offline)

        Args:
            city: Nome da cidade
            state: Sigla do estado (ex: SP, RJ)
            use_cache: Compatibilidade (GeoNames é sempre cache)

        Returns:
            Lista de nomes de bairros
        """
        if not city or not state:
            return []

        # Buscar do GeoNames (já é cache offline)
        print(f"        [BAIRROS] 🗂️  Buscando no GeoNames (offline) para {city}/{state}...")
        neighborhoods_data = self.cache.get_neighborhoods_from_geonames(city, state, limit=50)

        if not neighborhoods_data:
            print(f"        [BAIRROS] ⚠️  Nenhum bairro encontrado no GeoNames")
            return []

        # Extrair apenas nomes
        neighborhoods = [n['name'] for n in neighborhoods_data]
        
        # Filtrar e limpar
        neighborhoods = self._filter_neighborhoods(neighborhoods, city)

        if neighborhoods:
            print(f"        [BAIRROS] ✅ {len(neighborhoods)} bairros descobertos (GeoNames offline)")
        else:
            print(f"        [BAIRROS] ⚠️  Nenhum bairro válido após filtros")

        return neighborhoods

    def discover_neighborhoods_with_coords(self, city: str, state: str, limit: int = 50) -> List[Dict[str, any]]:
        """
        Descobre bairros com coordenadas para cálculo de distâncias
        
        Returns:
            Lista de dicionários com: name, latitude, longitude, population
        """
        if not city or not state:
            return []

        print(f"        [BAIRROS] 🗺️  Buscando bairros com coordenadas para {city}/{state}...")
        neighborhoods = self.cache.get_neighborhoods_from_geonames(city, state, limit=limit)

        if neighborhoods:
            print(f"        [BAIRROS] ✅ {len(neighborhoods)} bairros com coordenadas")
        else:
            print(f"        [BAIRROS] ⚠️  Nenhum bairro encontrado")


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
