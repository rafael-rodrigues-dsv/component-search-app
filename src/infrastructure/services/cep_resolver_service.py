"""
CEP Resolver Service - BrasilAPI com Cache
Normaliza respostas para manter compatibilidade com código existente
"""
from typing import Optional, Dict
import requests


class CepResolverService:
    """
    Serviço de resolução de CEP usando BrasilAPI com cache local

    Ordem de prioridade:
    1. Cache Local (instantâneo)
    2. BrasilAPI (API brasileira rápida e confiável)
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PythonSearchApp/4.0.0 (CEP Resolver)'
        })
        self.timeout = 10

        # Inicializar cache
        from ...infrastructure.cache.cep_cache import CepCache
        self.cache = CepCache()

        # Estatísticas (para análise)
        self.stats = {
            'cache': {'hits': 0, 'misses': 0},
            'brasilapi': {'success': 0, 'failures': 0}
        }

    def get_cep_data(self, cep: str) -> Optional[Dict]:
        """
        Busca dados do CEP com cache

        Args:
            cep: CEP com ou sem formatação (ex: "01310-100" ou "01310100")

        Returns:
            Dict com campos normalizados:
            {
                'cep': str,
                'localidade': str (cidade),
                'uf': str (estado),
                'bairro': str,
                'logradouro': str,
                'complemento': str,
                'source': str (qual fonte foi usada)
            }
        """
        clean_cep = self._clean_cep(cep)

        if not self._is_valid_cep(clean_cep):
            return None

        # 1. Tentar cache primeiro (instantâneo)
        cached_result = self.cache.get(clean_cep)
        if cached_result:
            self.stats['cache']['hits'] += 1
            return cached_result

        self.stats['cache']['misses'] += 1

        # 2. Buscar no BrasilAPI
        result = self._try_brasilapi(clean_cep)
        if result:
            self.stats['brasilapi']['success'] += 1
            normalized = self._normalize_response(result, cep)

            # Salvar no cache para próximas consultas
            self.cache.set(clean_cep, normalized)

            return normalized

        self.stats['brasilapi']['failures'] += 1

        # API falhou
        return None

    def _try_brasilapi(self, cep: str) -> Optional[Dict]:
        """Tenta buscar CEP via BrasilAPI"""
        try:
            url = f"https://brasilapi.com.br/api/cep/v2/{cep}"
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()

                # BrasilAPI retorna erro como campo
                if 'message' in data or 'errors' in data:
                    return None

                return data

            return None

        except Exception:
            return None

    def _normalize_response(self, data: dict, original_cep: str) -> Dict:
        """
        Normaliza resposta para formato padrão (compatível com código existente)

        Args:
            data: Dados brutos da BrasilAPI
            original_cep: CEP original informado pelo usuário

        Returns:
            Dict normalizado com campos em português
        """
        # Converter campos inglês → português (BrasilAPI usa inglês)
        normalized = {
            'cep': data.get('cep', original_cep),
            'localidade': data.get('city', ''),           # city → localidade
            'uf': data.get('state', ''),                  # state → uf
            'bairro': data.get('neighborhood', ''),       # neighborhood → bairro
            'logradouro': data.get('street', ''),         # street → logradouro
            'complemento': '',                             # BrasilAPI não tem complemento
            'source': 'brasilapi'
        }

        return normalized

    def _clean_cep(self, cep: str) -> str:
        """Remove formatação do CEP (mantém só números)"""
        if not cep:
            return ''
        return ''.join(filter(str.isdigit, str(cep)))

    def _is_valid_cep(self, cep: str) -> bool:
        """Valida se CEP tem formato correto (8 dígitos)"""
        return len(cep) == 8 and cep.isdigit()

    def get_stats(self) -> Dict:
        """Retorna estatísticas de uso"""
        cache_total = self.stats['cache']['hits'] + self.stats['cache']['misses']
        api_total = self.stats['brasilapi']['success'] + self.stats['brasilapi']['failures']
        total_requests = self.stats['cache']['misses']  # Só conta quando vai pra API

        if cache_total == 0:
            return {
                'total_requests': 0,
                'cache_hit_rate': '0%',
                'api_success_rate': '0%',
                'cache_stats': self.cache.get_stats()
            }

        cache_hit_rate = (self.stats['cache']['hits'] / cache_total * 100) if cache_total > 0 else 0
        api_success_rate = (self.stats['brasilapi']['success'] / api_total * 100) if api_total > 0 else 0

        return {
            'total_requests': cache_total,
            'cache_hits': self.stats['cache']['hits'],
            'cache_misses': self.stats['cache']['misses'],
            'cache_hit_rate': f"{cache_hit_rate:.1f}%",
            'api_success_rate': f"{api_success_rate:.1f}%",
            'stats': self.stats,
            'cache_stats': self.cache.get_stats()
        }
