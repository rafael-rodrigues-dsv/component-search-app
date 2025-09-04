"""
Serviço de geolocalização para calcular distâncias
"""
import re
import requests
import time
from math import radians, cos, sin, asin, sqrt
from typing import Optional, Tuple
import logging

class GeolocationService:
    """Serviço para geocodificação e cálculo de distâncias"""
    
    def __init__(self, cep_referencia: str = None):
        from config.settings import REFERENCE_CEP
        if cep_referencia is None:
            cep_referencia = REFERENCE_CEP
        self.logger = logging.getLogger(__name__)
        self.cep_referencia = cep_referencia
        self.lat_referencia = None
        self.lon_referencia = None
        self._inicializar_ponto_referencia()
    
    def _inicializar_ponto_referencia(self):
        """Inicializa coordenadas do ponto de referência"""
        try:
            lat, lon = self.geocodificar_cep(self.cep_referencia)
            if lat and lon:
                self.lat_referencia = lat
                self.lon_referencia = lon
                self.logger.info(f"Ponto de referência: {self.cep_referencia} ({lat}, {lon})")
            else:
                # Fallback: Centro de São Paulo
                self.lat_referencia = -23.5505
                self.lon_referencia = -46.6333
                self.logger.warning("Usando centro de SP como referência")
        except Exception as e:
            self.logger.error(f"Erro ao inicializar referência: {e}")
            self.lat_referencia = -23.5505
            self.lon_referencia = -46.6333
    
    def extrair_endereco_do_html(self, html_content: str, termo_busca: str) -> Optional[str]:
        """Extrai endereço do HTML - só geocodifica se encontrar endereço real"""
        if not html_content:
            return None
        
        # Cenário ideal: endereço completo
        endereco_completo = self._extrair_endereco_completo(html_content)
        if endereco_completo:
            return endereco_completo
        
        # Cenário parcial: cidade/bairro
        endereco_parcial = self._extrair_endereco_parcial(html_content)
        if endereco_parcial:
            return endereco_parcial
        
        # Sem fallback - só geocodifica endereços reais
        return None
    
    def _extrair_endereco_completo(self, html_content: str) -> Optional[str]:
        """Extrai endereço completo do HTML"""
        patterns = [
            r'(?:rua|av\.|avenida|alameda|travessa)\s+[^,\n]+,\s*\d+[^,\n]*,\s*[^,\n]+,\s*sp',
            r'(?:endereço|address)[:=]\s*([^<\n]+(?:rua|av\.|avenida)[^<\n]+sp)',
            r'(?:rua|av\.|avenida)\s+[^,\n]+,?\s*\d+[^,\n]*[^,\n]*são\s+paulo',
            r'\d{5}-?\d{3}[^<\n]*(?:rua|av\.|avenida)[^<\n]+',
            r'(?:rua|av\.|avenida)[^<\n]+\d{5}-?\d{3}'
        ]
        
        html_lower = html_content.lower()
        for pattern in patterns:
            matches = re.findall(pattern, html_lower, re.IGNORECASE | re.MULTILINE)
            if matches:
                endereco = matches[0].strip()
                if len(endereco) > 20:
                    return self._limpar_endereco(endereco)
        
        return None
    
    def _extrair_endereco_parcial(self, html_content: str) -> Optional[str]:
        """Extrai cidade/bairro do HTML"""
        patterns = [
            r'(?:moema|vila\s+mariana|pinheiros|itaim|jardins|centro|liberdade|bela\s+vista)',
            r'(?:campinas|guarulhos|santo\s+andré|são\s+bernardo|osasco|barueri)',
            r'(?:cidade|localização)[:=]\s*([^,<\n]+)',
            r'são\s+paulo\s*[-,]\s*sp'
        ]
        
        html_lower = html_content.lower()
        for pattern in patterns:
            matches = re.findall(pattern, html_lower, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], str):
                    cidade = matches[0].strip()
                else:
                    cidade = matches[0]
                return f"{cidade}, São Paulo, SP"
        
        return None
    

    
    def _limpar_endereco(self, endereco: str) -> str:
        """Limpa e formata endereço"""
        endereco = re.sub(r'<[^>]+>', '', endereco)
        endereco = re.sub(r'[^\w\s,.-]', '', endereco)
        endereco = ' '.join(endereco.split())
        return endereco.strip()
    
    def geocodificar_endereco(self, endereco: str) -> Tuple[Optional[float], Optional[float]]:
        """Converte endereço em coordenadas usando Nominatim"""
        if not endereco:
            return None, None
        
        try:
            if 'são paulo' not in endereco.lower():
                endereco += ', São Paulo, SP, Brasil'
            
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                'q': endereco,
                'format': 'json',
                'limit': 1,
                'countrycodes': 'br'
            }
            
            headers = {'User-Agent': 'PythonSearchApp/1.0'}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                return lat, lon
            
            time.sleep(1)
            return None, None
            
        except Exception as e:
            self.logger.error(f"Erro na geocodificação: {e}")
            return None, None
    
    def geocodificar_cep(self, cep: str) -> Tuple[Optional[float], Optional[float]]:
        """Geocodifica CEP usando ViaCEP + Nominatim"""
        try:
            cep_limpo = re.sub(r'\D', '', cep)
            if len(cep_limpo) != 8:
                return None, None
            
            url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'erro' in data:
                return None, None
            
            endereco = f"{data.get('logradouro', '')}, {data.get('bairro', '')}, {data.get('localidade', '')}, {data.get('uf', '')}"
            return self.geocodificar_endereco(endereco)
            
        except Exception as e:
            self.logger.error(f"Erro na geocodificação do CEP: {e}")
            return None, None
    
    def calcular_distancia(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula distância entre dois pontos usando fórmula de Haversine"""
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        return round(c * 6371, 2)
    
    def calcular_distancia_do_endereco(self, endereco: str) -> Tuple[Optional[str], Optional[float], Optional[float], Optional[float]]:
        """Calcula distância de um endereço até o ponto de referência"""
        if not endereco or not self.lat_referencia or not self.lon_referencia:
            return endereco, None, None, None
        
        lat, lon = self.geocodificar_endereco(endereco)
        if not lat or not lon:
            return endereco, None, None, None
        
        distancia = self.calcular_distancia(
            self.lat_referencia, self.lon_referencia, lat, lon
        )
        
        return endereco, lat, lon, distancia