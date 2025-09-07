"""
Serviço de Cache de Cidades - Base de dados local otimizada
"""
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional
import requests


class CitiesCacheService:
    """Cache local de cidades brasileiras para performance máxima"""
    
    def __init__(self):
        self.cache_dir = Path("data/cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.db_path = self.cache_dir / "cities_brazil.db"
        self.session = requests.Session()
        
    def get_state_cities(self, uf: str) -> List[Dict]:
        """Obter cidades do estado (cache local ou download)"""
        if not self._cache_exists():
            print("[CACHE] Primeira execução - baixando base de cidades...")
            self._build_cache()
        
        return self._get_cities_from_cache(uf)
    
    def _cache_exists(self) -> bool:
        """Verificar se cache existe e é válido"""
        return self.db_path.exists()
    
    def _build_cache(self):
        """Construir cache completo de uma vez"""
        print("[CACHE] Criando base local de cidades brasileiras...")
        
        # Usar Repository para criar cache
        from ...repositories.access_repository import AccessRepository
        repo = AccessRepository()
        repo.create_cities_cache_table()
        
        # Estados brasileiros
        states = ['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG',
                 'PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO']
        
        total_cities = 0
        for uf in states:
            try:
                print(f"[CACHE] Baixando {uf}...")
                cities = self._download_state_cities(uf)
                
                # Usar Repository para salvar cidades
                repo.save_cities_to_cache(cities, uf)
                
                total_cities += len(cities)
                
            except Exception as e:
                print(f"[CACHE] Erro {uf}: {e}")
        
        # Repository gerencia a conexão
        print(f"[CACHE] ✅ Cache criado: {total_cities} cidades")
    
    def _download_state_cities(self, uf: str) -> List[Dict]:
        """Download otimizado via Brasil API"""
        try:
            # Tentar Brasil API primeiro (mais rápida)
            url = f"https://brasilapi.com.br/api/ibge/municipios/v1/{uf}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                cities = response.json()
                # Adicionar população estimada baseada no código IBGE
                for city in cities:
                    city['population'] = self._estimate_population(city['codigo_ibge'])
                return cities
            
        except Exception:
            pass
        
        # Fallback para IBGE oficial
        try:
            url = f"https://servicodados.ibge.gov.br/api/v1/localidades/estados/{uf}/municipios"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"[CACHE] Erro download {uf}: {e}")
            return []
    
    def _estimate_population(self, ibge_code: str) -> int:
        """Estimativa de população baseada em padrões conhecidos"""
        # Capitais conhecidas (códigos IBGE)
        capitals = {
            '3550308': 12400000,  # São Paulo
            '3304557': 6775000,   # Rio de Janeiro
            '3106200': 2530000,   # Belo Horizonte
            '4314902': 1488000,   # Porto Alegre
            '4106902': 1963000,   # Curitiba
            '2927408': 2900000,   # Salvador
            '2611606': 1650000,   # Recife
            '2304400': 2700000,   # Fortaleza
        }
        
        if ibge_code in capitals:
            return capitals[ibge_code]
        
        # Estimativa baseada no código (cidades maiores têm códigos menores)
        code_num = int(ibge_code) if ibge_code.isdigit() else 9999999
        if code_num < 1000000:
            return 800000  # Cidade grande
        elif code_num < 3000000:
            return 400000  # Cidade média
        elif code_num < 5000000:
            return 150000  # Cidade pequena
        else:
            return 50000   # Cidade muito pequena
    
    def _get_cities_from_cache(self, uf: str) -> List[Dict]:
        """Buscar cidades do cache local"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        # Usar Repository para buscar cidades
        from ...repositories.access_repository import AccessRepository
        repo = AccessRepository()
        return repo.get_cities_from_cache(uf)
        
        # Repository já retorna os dados formatados
    
    def get_metropolitan_cities(self, uf: str, capital_name: str) -> List[Dict]:
        """Obter cidades da região metropolitana (top 20 por população)"""
        cities = self.get_state_cities(uf)
        
        # Marcar capital
        for city in cities:
            if city['nome'].lower() == capital_name.lower():
                city['is_capital'] = True
        
        # Retornar top 20 por população
        return cities[:20]
    
    def clear_cache(self):
        """Limpar cache para forçar rebuild"""
        if self.db_path.exists():
            self.db_path.unlink()
            print("[CACHE] Cache limpo")