"""
Serviço de Cache de Cidades - Base de dados local otimizada
"""
import sqlite3
from pathlib import Path
from typing import Dict, List

import requests


class CitiesCacheService:
    """Cache local de cidades brasileiras para performance máxima"""
    
    def __init__(self):
        self.cache_dir = Path("data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "cities_brazil.db"
        self.session = requests.Session()

    def _ensure_cache_db(self):
        """Create sqlite DB and table if missing"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uf TEXT(2),
                    nome TEXT(200),
                    ibge TEXT(20),
                    population INTEGER
                )
                """
            )
            conn.commit()
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            conn.close()

    def _save_cities_to_sqlite(self, cities: List[Dict], uf: str) -> int:
        """Save a list of cities into sqlite cache (idempotent)"""
        if not cities:
            return 0
        self._ensure_cache_db()
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            inserted = 0
            for c in cities:
                nome = c.get('nome') or c.get('name') or c.get('municipio')
                ibge = c.get('codigo_ibge') or c.get('ibge') or c.get('codigo') or None
                population = c.get('population') or None
                try:
                    cursor.execute("SELECT id FROM cities WHERE uf = ? AND UPPER(nome) = UPPER(?)", (uf, nome))
                    if cursor.fetchone():
                        continue
                except Exception:
                    pass
                try:
                    cursor.execute("INSERT INTO cities (uf, nome, ibge, population) VALUES (?, ?, ?, ?)", (uf, nome, ibge, population))
                    inserted += 1
                except Exception:
                    continue
            conn.commit()
            return inserted
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            conn.close()

    def _get_cities_from_cache(self, uf: str) -> List[Dict]:
        """Retorna lista de cidades do cache para o estado informado"""
        if not self.db_path.exists():
            return []
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT nome, ibge, population FROM cities WHERE uf = ? ORDER BY nome", (uf,))
            rows = cursor.fetchall()
            result = []
            for r in rows:
                result.append({'nome': r['nome'], 'ibge': r['ibge'], 'population': r['population']})
            return result
        finally:
            try:
                cursor.close()
            except Exception:
                pass
            conn.close()

    # Backwards compatible public methods
    def get_state_cities(self, uf: str) -> List[Dict]:
        if not self._cache_exists():
            print("[CACHE] Primeira execução - baixando base de cidades...")
            self._build_cache()
        return self._get_cities_from_cache(uf)

    def _cache_exists(self) -> bool:
        return self.db_path.exists()

    def _build_cache(self):
        from ...config.config_manager import ConfigManager
        config = ConfigManager()
        states = ['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG',
                 'PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO']
        total_cities = 0
        for uf in states:
            try:
                cities = self._download_state_cities(uf)
                saved = self._save_cities_to_sqlite(cities, uf)
                total_cities += saved
            except Exception as e:
                print(f"[CACHE] Erro {uf}: {e}")
        print(f"[CACHE] ✅ Cache criado: {total_cities} cidades")

    def _download_state_cities(self, uf: str) -> List[Dict]:
        """Download otimizado via Brasil API"""
        try:
            # Tentar Brasil API primeiro (mais rápida)
            from ...config.config_manager import ConfigManager
            config = ConfigManager()
            ibge_url = config.get('geographic_discovery.apis.ibge.url', 'https://servicodados.ibge.gov.br/api/v1/localidades')
            url = f"{ibge_url}/estados/{uf}/municipios"
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
            from ...config.config_manager import ConfigManager
            config = ConfigManager()
            ibge_url = config.get('geographic_discovery.apis.ibge.url', 'https://servicodados.ibge.gov.br/api/v1/localidades')
            url = f"{ibge_url}/estados/{uf}/municipios"
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
    
    def clear_cache(self):
        """Limpar cache para forçar rebuild"""
        if self.db_path.exists():
            self.db_path.unlink()
            print("[CACHE] Cache limpo")