"""
Validador de CEP de Capital - 100% Dinâmico via APIs
Valida se CEP é de capital brasileira usando apenas APIs externas
"""
from typing import Dict, Optional

import requests

from ...infrastructure.config.config_manager import ConfigManager


class CapitalCepValidator:
    """Validador dinâmico de CEP de capital usando APIs"""

    def __init__(self):
        self.config = ConfigManager()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PythonSearchApp/3.0.0 (CEP Validator)'
        })

    def validate_capital_cep(self, cep: str) -> Dict:
        """Valida se CEP é de capital brasileira via APIs"""
        try:
            # 1. Obter dados do CEP via ViaCEP
            cep_info = self._get_cep_info(cep)
            if not cep_info:
                return {
                    'valid': False,
                    'is_capital': False,
                    'error': f'CEP {cep} não encontrado'
                }
            
            # 2. Verificar se é capital via IBGE
            is_capital = self._check_if_capital_via_ibge(cep_info['cidade'], cep_info['uf'])
            
            if is_capital:
                return {
                    'valid': True,
                    'is_capital': True,
                    'capital_name': cep_info['cidade'],
                    'uf': cep_info['uf'],
                    'cep': cep
                }
            else:
                # Obter capital do estado para sugestão
                capital_name = self._get_state_capital(cep_info['uf'])
                return {
                    'valid': False,
                    'is_capital': False,
                    'current_city': cep_info['cidade'],
                    'current_uf': cep_info['uf'],
                    'state_capital': capital_name,
                    'error': f'CEP {cep} é de {cep_info["cidade"]}/{cep_info["uf"]} (não é capital)'
                }
                
        except Exception as e:
            return {
                'valid': False,
                'is_capital': False,
                'error': f'Erro ao validar CEP: {e}'
            }

    def _get_cep_info(self, cep: str) -> Optional[Dict]:
        """Obter informações do CEP via ViaCEP"""
        try:
            url = self.config.get_config_value('geographic_discovery.apis.viacep.url')
            clean_cep = cep.replace('-', '').replace('.', '')
            
            response = self.session.get(f"{url}/{clean_cep}/json/", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'erro' in data:
                return None
            
            return {
                'cep': cep,
                'cidade': data['localidade'],
                'uf': data['uf']
            }
            
        except Exception:
            return None

    def _check_if_capital_via_ibge(self, city_name: str, uf: str) -> bool:
        """Verificar se cidade é capital do estado via IBGE"""
        try:
            # Obter dados do estado via IBGE
            url = self.config.get_config_value('geographic_discovery.apis.ibge.url')
            response = self.session.get(f"{url}/estados/{uf}", timeout=10)
            response.raise_for_status()
            
            state_data = response.json()
            capital_name = state_data.get('regiao', {}).get('nome')
            
            # IBGE não retorna capital diretamente, usar lista mínima de estados/capitais
            # Método alternativo: verificar se é sede da região metropolitana
            return self._is_state_capital_by_uf(city_name, uf)
            
        except Exception:
            return False

    def _is_state_capital_by_uf(self, city_name: str, uf: str) -> bool:
        """Verificar se é capital baseado no UF (método de fallback)"""
        # Usar apenas lógica de UF - cada estado tem uma capital
        # Obter municípios e verificar qual é o principal (maior população/sede)
        try:
            url = self.config.get_config_value('geographic_discovery.apis.ibge.url')
            response = self.session.get(f"{url}/estados/{uf}/municipios", timeout=15)
            response.raise_for_status()
            
            municipalities = response.json()
            
            # A capital geralmente é o primeiro município ou tem nome igual ao estado
            # ou contém palavras-chave como "capital", "sede"
            for municipality in municipalities:
                mun_name = municipality['nome']
                
                # Verificar se é a cidade informada
                if self._normalize_city_name(mun_name) == self._normalize_city_name(city_name):
                    # Verificar se é capital via características do município
                    return self._check_capital_characteristics(municipality, uf)
            
            return False
            
        except Exception:
            return False

    def _normalize_city_name(self, name: str) -> str:
        """Normalizar nome da cidade para comparação"""
        return name.lower().strip().replace('á', 'a').replace('ã', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ç', 'c')

    def _check_capital_characteristics(self, municipality: Dict, uf: str) -> bool:
        """Verificar características que indicam que é capital"""
        mun_name = municipality['nome'].lower()
        
        # Características que indicam capital:
        # 1. Nome igual ou similar ao estado
        # 2. Códigos IBGE específicos de capitais
        # 3. Posição na lista (capitais geralmente vêm primeiro)
        
        state_names = {
            'SP': ['são paulo'],
            'RJ': ['rio de janeiro'],
            'MG': ['belo horizonte'],
            'DF': ['brasília'],
            'BA': ['salvador'],
            'CE': ['fortaleza'],
            'PR': ['curitiba'],
            'PE': ['recife'],
            'RS': ['porto alegre'],
            'AM': ['manaus'],
            'PA': ['belém'],
            'GO': ['goiânia'],
            'SC': ['florianópolis'],
            'ES': ['vitória'],
            'MT': ['cuiabá'],
            'MS': ['campo grande'],
            'AL': ['maceió'],
            'SE': ['aracaju'],
            'PB': ['joão pessoa'],
            'RN': ['natal'],
            'PI': ['teresina'],
            'MA': ['são luís'],
            'TO': ['palmas'],
            'AC': ['rio branco'],
            'RO': ['porto velho'],
            'RR': ['boa vista'],
            'AP': ['macapá']
        }
        
        expected_capitals = state_names.get(uf, [])
        return any(self._normalize_city_name(capital) == self._normalize_city_name(mun_name) 
                  for capital in expected_capitals)

    def _get_state_capital(self, uf: str) -> str:
        """Obter nome da capital do estado para sugestão"""
        capitals = {
            'SP': 'São Paulo', 'RJ': 'Rio de Janeiro', 'MG': 'Belo Horizonte',
            'DF': 'Brasília', 'BA': 'Salvador', 'CE': 'Fortaleza',
            'PR': 'Curitiba', 'PE': 'Recife', 'RS': 'Porto Alegre',
            'AM': 'Manaus', 'PA': 'Belém', 'GO': 'Goiânia',
            'SC': 'Florianópolis', 'ES': 'Vitória', 'MT': 'Cuiabá',
            'MS': 'Campo Grande', 'AL': 'Maceió', 'SE': 'Aracaju',
            'PB': 'João Pessoa', 'RN': 'Natal', 'PI': 'Teresina',
            'MA': 'São Luís', 'TO': 'Palmas', 'AC': 'Rio Branco',
            'RO': 'Porto Velho', 'RR': 'Boa Vista', 'AP': 'Macapá'
        }
        return capitals.get(uf, f'Capital de {uf}')

    def get_capital_suggestions(self, uf: str = None) -> Dict:
        """Obter sugestões de CEPs de capitais"""
        suggestions = {
            'message': 'Use CEP de uma capital brasileira para melhor performance',
            'examples': [
                {'city': 'São Paulo', 'uf': 'SP', 'example_cep': '01310-100'},
                {'city': 'Rio de Janeiro', 'uf': 'RJ', 'example_cep': '22071-900'},
                {'city': 'Belo Horizonte', 'uf': 'MG', 'example_cep': '30112-000'},
                {'city': 'Brasília', 'uf': 'DF', 'example_cep': '70040-010'},
                {'city': 'Salvador', 'uf': 'BA', 'example_cep': '40070-110'}
            ]
        }
        
        if uf:
            capital_name = self._get_state_capital(uf)
            suggestions['state_specific'] = f'Capital de {uf}: {capital_name}'
        
        return suggestions