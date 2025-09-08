"""
Serviço de geolocalização otimizado e robusto
"""
import logging
import queue
import re
import threading
import time
from dataclasses import dataclass
from math import radians, cos, sin, asin, sqrt
from typing import Optional, Tuple, List

import requests


@dataclass
class GeoResult:
    """Resultado da geocodificação"""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_km: Optional[float] = None
    address: Optional[str] = None
    success: bool = False


class GeolocationService:
    """Serviço otimizado para geocodificação e cálculo de distâncias"""

    def __init__(self, cep_referencia: str = None):
        from src.infrastructure.config.config_manager import ConfigManager
        config = ConfigManager()
        self.logger = logging.getLogger(__name__)
        self.cep_referencia = cep_referencia or config.reference_cep
        self.lat_referencia = None
        self.lon_referencia = None
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'PythonSearchApp/2.2.2'})
        self._inicializar_ponto_referencia()

    def _inicializar_ponto_referencia(self):
        """Inicializa coordenadas do ponto de referência"""
        try:
            result = self._geocodificar_cep_interno(self.cep_referencia)
            if result.success:
                self.lat_referencia = result.latitude
                self.lon_referencia = result.longitude
                self.logger.info(f"Ponto de referência: {self.cep_referencia} ({result.latitude}, {result.longitude})")
            else:
                self._usar_fallback_sao_paulo()
        except Exception as e:
            self.logger.error(f"Erro ao inicializar referência: {self._sanitize_log(str(e))}")
            self._usar_fallback_sao_paulo()

    def _usar_fallback_sao_paulo(self):
        """Usa centro de São Paulo como fallback"""
        self.lat_referencia = -23.5505
        self.lon_referencia = -46.6333
        self.logger.warning("Usando centro de SP como referência")

    def _sanitize_log(self, text: str) -> str:
        """Sanitiza texto para logs evitando log injection"""
        return re.sub(r'[\r\n\t]', ' ', str(text)[:100])

    def extrair_endereco_do_html(self, html_content: str, termo_busca: str = None) -> Optional[str]:
        """Extrai endereço do HTML usando AddressExtractor"""
        from src.infrastructure.utils.address_extractor import AddressExtractor
        return AddressExtractor.extract_from_html(html_content)

    def geocodificar_endereco_estruturado(self, address_model) -> GeoResult:
        """Converte AddressModel em coordenadas (método otimizado)"""
        if not address_model or not address_model.is_valid():
            return GeoResult()

        self.logger.info(f"[GEO] Geocodificando estruturado: {address_model.logradouro}")

        # Usar campos estruturados diretamente
        result = self._geocodificar_structured_model(address_model)
        if result.success:
            return result

        # Fallback para string completa
        endereco_str = address_model.to_full_address()
        return self._geocodificar_freeform(endereco_str)
    
    def geocodificar_endereco(self, endereco: str) -> GeoResult:
        """Converte endereço string em coordenadas (método legado)"""
        if not endereco:
            return GeoResult()

        self.logger.info(f"[GEO] Geocodificando: {self._sanitize_log(endereco)}")

        # Tentar structured query primeiro
        result = self._geocodificar_structured(endereco)
        if result.success:
            return result

        # Fallback para free-form query
        return self._geocodificar_freeform(endereco)

    def _geocodificar_structured_model(self, address_model) -> GeoResult:
        """Geocodificação usando AddressModel estruturado com fallback progressivo"""
        
        # Tentativa 1: Endereço completo
        if address_model.logradouro:
            result = self._try_geocode_with_params({
                'street': f"{address_model.logradouro} {address_model.numero}".strip(),
                'city': address_model.cidade,
                'state': address_model.estado,
                'country': 'Brazil'
            }, "endereço completo")
            if result.success:
                return result
        
        # Tentativa 2: Só CEP (se disponível)
        if address_model.cep:
            result = self._try_geocode_with_params({
                'postalcode': address_model.cep,
                'country': 'Brazil'
            }, "CEP")
            if result.success:
                return result
        
        # Tentativa 3: Bairro + Cidade
        if address_model.bairro:
            result = self._try_geocode_with_params({
                'city': f"{address_model.bairro}, {address_model.cidade}",
                'state': address_model.estado,
                'country': 'Brazil'
            }, "bairro")
            if result.success:
                return result
        
        # Tentativa 4: Só Cidade
        result = self._try_geocode_with_params({
            'city': address_model.cidade,
            'state': address_model.estado,
            'country': 'Brazil'
        }, "cidade")
        
        return result
    
    def _try_geocode_with_params(self, params: dict, tipo: str) -> GeoResult:
        """Tenta geocodificar com parâmetros específicos"""
        try:
            from src.infrastructure.config.config_manager import ConfigManager
            config = ConfigManager()
            nominatim_url = config.get('geographic_discovery.apis.nominatim.url', 'https://nominatim.openstreetmap.org')
            
            params.update({
                'format': 'json',
                'limit': 1,
                'addressdetails': 0
            })

            response = self.session.get(
                f"{nominatim_url}/search",
                params=params,
                timeout=5
            )
            response.raise_for_status()

            data = response.json()
            if data:
                lat, lon = float(data[0]['lat']), float(data[0]['lon'])
                self.logger.info(f"[GEO] Structured {tipo} OK: {lat}, {lon}")
                return GeoResult(latitude=lat, longitude=lon, success=True)

        except requests.RequestException as e:
            self.logger.debug(f"[GEO] {tipo} - erro de rede: {self._sanitize_log(str(e))}")
        except (ValueError, KeyError) as e:
            self.logger.debug(f"[GEO] {tipo} - erro de parsing: {self._sanitize_log(str(e))}")
        except Exception as e:
            self.logger.debug(f"[GEO] {tipo} - erro inesperado: {self._sanitize_log(str(e))}")

        return GeoResult()
    
    def _geocodificar_structured(self, endereco: str) -> GeoResult:
        """Geocodificação estruturada"""
        try:
            street, city, state = self._parse_endereco(endereco)
            if not street:
                return GeoResult()

            params = {
                'street': street,
                'city': city,
                'state': state,
                'country': 'Brazil',
                'format': 'json',
                'limit': 1,
                'addressdetails': 0
            }

            from src.infrastructure.config.config_manager import ConfigManager
            config = ConfigManager()
            nominatim_url = config.get('geographic_discovery.apis.nominatim.url', 'https://nominatim.openstreetmap.org')
            
            response = self.session.get(
                f"{nominatim_url}/search",
                params=params,
                timeout=5
            )
            response.raise_for_status()

            data = response.json()
            if data:
                lat, lon = float(data[0]['lat']), float(data[0]['lon'])
                self.logger.info(f"[GEO] Structured OK: {lat}, {lon}")
                return GeoResult(latitude=lat, longitude=lon, success=True)

        except requests.RequestException as e:
            self.logger.warning(f"[GEO] Erro de rede: {self._sanitize_log(str(e))}")
        except (ValueError, KeyError) as e:
            self.logger.debug(f"[GEO] Erro de parsing: {self._sanitize_log(str(e))}")
        except Exception as e:
            self.logger.error(f"[GEO] Erro inesperado: {self._sanitize_log(str(e))}")

        return GeoResult()

    def _geocodificar_freeform(self, endereco: str) -> GeoResult:
        """Geocodificação free-form com rate limiting"""
        variants = self._gerar_variantes_endereco(endereco)

        for i, variant in enumerate(variants, 1):
            try:
                params = {
                    'q': variant,
                    'format': 'json',
                    'limit': 1,
                    'countrycodes': 'br',
                    'addressdetails': 0
                }

                from src.infrastructure.config.config_manager import ConfigManager
                config = ConfigManager()
                nominatim_url = config.get('geographic_discovery.apis.nominatim.url', 'https://nominatim.openstreetmap.org')
                
                response = self.session.get(
                    f"{nominatim_url}/search",
                    params=params,
                    timeout=5
                )
                response.raise_for_status()

                data = response.json()
                if data:
                    lat, lon = float(data[0]['lat']), float(data[0]['lon'])
                    self.logger.info(f"[GEO] Freeform OK: {lat}, {lon}")
                    return GeoResult(latitude=lat, longitude=lon, success=True)

                # Rate limiting apenas entre tentativas
                if i < len(variants):
                    time.sleep(0.5)

            except requests.RequestException as e:
                self.logger.warning(f"[GEO] Tentativa {i} - erro de rede: {self._sanitize_log(str(e))}")
            except (ValueError, KeyError) as e:
                self.logger.debug(f"[GEO] Tentativa {i} - erro de parsing: {self._sanitize_log(str(e))}")
            except Exception as e:
                self.logger.error(f"[GEO] Tentativa {i} - erro inesperado: {self._sanitize_log(str(e))}")

        self.logger.warning(f"[GEO] Falha total: {self._sanitize_log(endereco)}")
        return GeoResult()

    def _parse_endereco(self, endereco: str) -> Tuple[str, str, str]:
        """Parse endereço para structured query"""
        endereco_limpo = self._normalizar_endereco(endereco)

        # Extrair informações da cidade e estado do próprio endereço
        city_match = re.search(r'([^,]+),\s*([^,]+),\s*([^,]+)$', endereco_limpo)
        if city_match:
            city = city_match.group(2).strip()
            state = city_match.group(3).strip()
        else:
            city, state = "São Paulo", "SP"

        # Extrair rua/avenida
        street_match = re.search(r'((?:avenida|av\.|rua|alameda)\s+[^,\d]+(?:\s+\d+)?)', endereco_limpo, re.IGNORECASE)
        street = street_match.group(1).strip() if street_match else ""

        return street, city, state

    def _gerar_variantes_endereco(self, endereco: str) -> List[str]:
        """Gera variações do endereço"""
        endereco_limpo = self._normalizar_endereco(endereco)
        variants = [endereco_limpo]

        # Normalizar "av." para "avenida"
        if 'av.' in endereco_limpo.lower():
            endereco_av = re.sub(r'\bav\.?\s+', 'avenida ', endereco_limpo, flags=re.IGNORECASE)
            variants.append(endereco_av)

        return variants[:2]

    def _normalizar_endereco(self, endereco: str) -> str:
        """Normaliza endereço já formatado pelo AddressExtractor"""
        # AddressExtractor já faz a formatação, apenas garantir consistência
        return endereco.strip()

    def _geocodificar_cep_interno(self, cep: str) -> GeoResult:
        """Geocodifica CEP usando ViaCEP + Nominatim"""
        try:
            cep_limpo = re.sub(r'\D', '', cep)
            if len(cep_limpo) != 8:
                return GeoResult()

            self.logger.debug(f"[GEO] Geocodificando CEP: {cep}")

            # Rate limiting para ViaCEP
            time.sleep(0.3)

            from src.infrastructure.config.config_manager import ConfigManager
            config = ConfigManager()
            viacep_url = config.get('geographic_discovery.apis.viacep.url', 'https://viacep.com.br/ws')
            
            response = self.session.get(f"{viacep_url}/{cep_limpo}/json/", timeout=5)
            response.raise_for_status()

            data = response.json()
            if 'erro' in data:
                return GeoResult()

            endereco = f"{data.get('logradouro', '')}, {data.get('bairro', '')}, {data.get('localidade', '')}, {data.get('uf', '')}"
            return self.geocodificar_endereco(endereco)

        except requests.exceptions.Timeout:
            self.logger.warning(f"[GEO] Timeout na consulta do CEP: {cep}")
        except requests.RequestException as e:
            self.logger.warning(f"[GEO] Erro de rede no CEP {cep}: {self._sanitize_log(str(e))}")
        except Exception as e:
            self.logger.error(f"[GEO] Erro inesperado no CEP {cep}: {self._sanitize_log(str(e))}")

        return GeoResult()

    def geocodificar_cep(self, cep: str) -> Tuple[Optional[float], Optional[float]]:
        """Interface pública para geocodificação de CEP"""
        result = self._geocodificar_cep_interno(cep)
        return result.latitude, result.longitude

    def calcular_distancia(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula distância usando fórmula de Haversine"""
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))

        return round(c * 6371, 2)

    def calcular_distancia_do_endereco(self, endereco: str) -> Tuple[
        Optional[str], Optional[float], Optional[float], Optional[float]]:
        """Calcula distância de um endereço até o ponto de referência com timeout"""
        if not endereco or not self.lat_referencia or not self.lon_referencia:
            return endereco, None, None, None

        try:
            result_queue = queue.Queue()

            def geocode_worker():
                try:
                    result = self.geocodificar_endereco(endereco)
                    result_queue.put(result)
                except Exception as e:
                    result_queue.put(GeoResult())

            thread = threading.Thread(target=geocode_worker)
            thread.daemon = True
            thread.start()
            thread.join(timeout=10)

            if thread.is_alive():
                self.logger.warning("[GEO] TIMEOUT (10s) - Geocodificação cancelada")
                return endereco, None, None, None

            try:
                result = result_queue.get_nowait()
            except queue.Empty:
                return endereco, None, None, None

            if not result.success:
                return endereco, None, None, None

            distancia = self.calcular_distancia(
                self.lat_referencia, self.lon_referencia,
                result.latitude, result.longitude
            )

            self.logger.info(f"[GEO] Distância calculada: {distancia}km")
            return endereco, result.latitude, result.longitude, distancia

        except Exception as e:
            self.logger.error(f"[GEO] Erro inesperado: {self._sanitize_log(str(e))}")
            return endereco, None, None, None
