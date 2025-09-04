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
        """Extrai endereço completo do HTML com limpeza avançada"""
        patterns = [
            # Padrão com CEP no início (caso 2 e 3)
            r'(\d{5}-?\d{3})[^a-zA-Z]*([^,\n]*(?:rua|av\.|avenida|alameda)[^,\n]+[^,\n]*são\s*paulo[^,\n]*)',
            # Padrão tradicional melhorado
            r'(?:rua|av\.|avenida|alameda|travessa)\s+[^,\n]+,?\s*\d+[^,\n]*[^,\n]*(?:são\s*paulo|sp)',
            # Padrão com endereço estruturado
            r'(?:endereço|address)[:=]\s*([^<\n]+(?:rua|av\.|avenida)[^<\n]+(?:são\s*paulo|sp))',
            # Padrão específico para caso 1
            r'(av\.?\s*[^\d]*\d+[^,]*(?:vila|jardim|bairro)[^,]*são\s*paulo)',
            # Padrão com aria-label (caso 2)
            r'aria-label[^>]*([^,]+,\s*\d+[^,]*[^,]*são\s*paulo[^,]*)',
            # Padrão genérico com limpeza
            r'([^\n]*(?:rua|av\.|avenida)[^\n]*\d+[^\n]*são\s*paulo[^\n]*)',
        ]
        
        html_lower = html_content.lower()
        for pattern in patterns:
            matches = re.findall(pattern, html_lower, re.IGNORECASE | re.MULTILINE)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        # Para padrões com grupos, junta os grupos
                        endereco = ' '.join([m for m in match if m]).strip()
                    else:
                        endereco = match.strip()
                    
                    endereco_limpo = self._limpar_endereco_avancado(endereco)
                    if len(endereco_limpo) > 15 and self._validar_endereco(endereco_limpo):
                        return endereco_limpo
        
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
    

    
    def _limpar_endereco_avancado(self, endereco: str) -> str:
        """Limpeza avançada de endereço com remoção de ruídos"""
        # Remove tags HTML
        endereco = re.sub(r'<[^>]+>', '', endereco)
        
        # Remove termos técnicos comuns
        ruidos = [
            r'aria-label[^\s]*', r'title[^\s]*', r'amp[^\s]*', r'zoom\d+',
            r'quot[^\s]*', r'url[^\s]*', r'http[^\s]*', r'maps\.google[^\s]*',
            r'section[^\s]*', r'main_block[^\s]*', r'action[^\s]*', r'address[^\s]*',
            r'adv_address[^\s]*', r'id[^\s]*', r'copy_lo[^\s]*', r'log[^\s]*'
        ]
        
        for ruido in ruidos:
            endereco = re.sub(ruido, '', endereco, flags=re.IGNORECASE)
        
        # Remove caracteres especiais exceto vírgulas, pontos e hífens
        endereco = re.sub(r'[^\w\s,.\-]', ' ', endereco)
        
        # Remove números isolados no final (IDs, códigos)
        endereco = re.sub(r'\s+\d{6,}\s*$', '', endereco)
        
        # Normaliza espaços
        endereco = ' '.join(endereco.split())
        
        # Garante que termina com São Paulo se não tiver
        if 'são paulo' not in endereco.lower() and 'sp' not in endereco.lower():
            endereco += ', São Paulo, SP'
        
        return endereco.strip()
    
    def _validar_endereco(self, endereco: str) -> bool:
        """Valida se o endereço extraído é válido"""
        endereco_lower = endereco.lower()
        
        # Deve ter pelo menos um tipo de logradouro
        tipos_logradouro = ['rua', 'av.', 'avenida', 'alameda', 'travessa', 'praça']
        tem_logradouro = any(tipo in endereco_lower for tipo in tipos_logradouro)
        
        # Deve ter São Paulo
        tem_sao_paulo = 'são paulo' in endereco_lower or 'sp' in endereco_lower
        
        # Não deve ter muitos números seguidos (IDs, códigos)
        tem_muitos_numeros = len(re.findall(r'\d{6,}', endereco)) > 1
        
        return tem_logradouro and tem_sao_paulo and not tem_muitos_numeros
    
    def _limpar_endereco(self, endereco: str) -> str:
        """Limpa e formata endereço (método legado)"""
        return self._limpar_endereco_avancado(endereco)
    
    def geocodificar_endereco(self, endereco: str) -> Tuple[Optional[float], Optional[float]]:
        """Converte endereço em coordenadas usando Nominatim com timeout agressivo"""
        if not endereco:
            return None, None
        
        self.logger.info(f"[GEO] Iniciando geocodificação: {endereco[:50]}...")
        
        # Lista de variações do endereço para tentar (máximo 2 para evitar travamento)
        endereco_variants = self._gerar_variantes_endereco(endereco)[:2]
        
        for i, variant in enumerate(endereco_variants, 1):
            try:
                self.logger.debug(f"[GEO] Tentativa {i}/{len(endereco_variants)}: {variant[:30]}...")
                
                url = "https://nominatim.openstreetmap.org/search"
                params = {
                    'q': variant,
                    'format': 'json',
                    'limit': 1,
                    'countrycodes': 'br'
                }
                
                headers = {'User-Agent': 'PythonSearchApp/2.2.2'}
                
                # Timeout agressivo de 5 segundos
                response = requests.get(url, params=params, headers=headers, timeout=5)
                response.raise_for_status()
                
                data = response.json()
                if data:
                    lat = float(data[0]['lat'])
                    lon = float(data[0]['lon'])
                    self.logger.info(f"[GEO] ✅ Sucesso: {variant[:30]}... -> {lat}, {lon}")
                    return lat, lon
                
                # Rate limiting reduzido
                time.sleep(0.5)
                
            except requests.exceptions.Timeout:
                self.logger.warning(f"[GEO] ⏱️ Timeout na tentativa {i}: {variant[:30]}...")
                continue
            except Exception as e:
                self.logger.debug(f"[GEO] ❌ Falha na tentativa {i}: {str(e)[:50]}...")
                continue
        
        self.logger.warning(f"[GEO] ❌ Falha total na geocodificação: {endereco[:50]}...")
        return None, None
    
    def _gerar_variantes_endereco(self, endereco: str) -> list:
        """Gera variações do endereço para melhorar geocodificação"""
        endereco_limpo = self._normalizar_endereco_para_geocodificacao(endereco)
        variants = []
        
        # Variante 1: Endereço original limpo
        variants.append(endereco_limpo)
        
        # Variante 2: Sem número (para ruas que não existem o número)
        endereco_sem_numero = re.sub(r',?\s*\d+[a-zA-Z]*\s*', ' ', endereco_limpo)
        endereco_sem_numero = re.sub(r'\s+', ' ', endereco_sem_numero).strip()
        if endereco_sem_numero != endereco_limpo:
            variants.append(endereco_sem_numero)
        
        # Variante 3: Apenas rua + cidade
        match = re.search(r'((?:rua|av\.|avenida|alameda)\s+[^,]+)', endereco_limpo, re.IGNORECASE)
        if match:
            rua_simples = match.group(1) + ', São Paulo, SP, Brasil'
            variants.append(rua_simples)
        
        # Variante 4: Apenas bairro + cidade (para casos como "vila curuçá")
        match_bairro = re.search(r'(vila|jardim|bairro)\s+([^,\s]+(?:\s+[^,\s]+)?)', endereco_limpo, re.IGNORECASE)
        if match_bairro:
            bairro = f"{match_bairro.group(1)} {match_bairro.group(2)}, São Paulo, SP, Brasil"
            variants.append(bairro)
        
        return variants
    
    def _normalizar_endereco_para_geocodificacao(self, endereco: str) -> str:
        """Normaliza endereço especificamente para geocodificação"""
        # Remove ruídos comuns
        endereco = re.sub(r'\s*-\s*nbsp\s*', ' ', endereco)
        endereco = re.sub(r'\s*cep\s*\d{5}-?\d{3}\s*', ' ', endereco, flags=re.IGNORECASE)
        endereco = re.sub(r'\s+sp\s+sp\s*', ' SP ', endereco, flags=re.IGNORECASE)
        endereco = re.sub(r'\s*-\s*são\s+josé\s+dos\s+c\s*', ', São José dos Campos, SP', endereco, flags=re.IGNORECASE)
        
        # Normaliza espaços
        endereco = re.sub(r'\s+', ' ', endereco).strip()
        
        # Garante que termina com Brasil
        if 'brasil' not in endereco.lower():
            if 'sp' in endereco.lower():
                endereco += ', Brasil'
            else:
                endereco += ', São Paulo, SP, Brasil'
        
        return endereco
    
    def geocodificar_cep(self, cep: str) -> Tuple[Optional[float], Optional[float]]:
        """Geocodifica CEP usando ViaCEP + Nominatim com timeout"""
        try:
            cep_limpo = re.sub(r'\D', '', cep)
            if len(cep_limpo) != 8:
                return None, None
            
            self.logger.debug(f"[GEO] Geocodificando CEP: {cep}")
            
            url = f"https://viacep.com.br/ws/{cep_limpo}/json/"
            response = requests.get(url, timeout=5)  # Timeout reduzido
            response.raise_for_status()
            
            data = response.json()
            if 'erro' in data:
                return None, None
            
            endereco = f"{data.get('logradouro', '')}, {data.get('bairro', '')}, {data.get('localidade', '')}, {data.get('uf', '')}"
            return self.geocodificar_endereco(endereco)
            
        except requests.exceptions.Timeout:
            self.logger.warning(f"[GEO] ⏱️ Timeout na consulta do CEP: {cep}")
            return None, None
        except Exception as e:
            self.logger.error(f"[GEO] ❌ Erro na geocodificação do CEP {cep}: {str(e)[:50]}...")
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
        """Calcula distância de um endereço até o ponto de referência com timeout Windows-compatível"""
        if not endereco or not self.lat_referencia or not self.lon_referencia:
            self.logger.debug(f"[GEO] Pulando - sem endereco ou referencia")
            return endereco, None, None, None
        
        try:
            # Timeout usando threading (compatível com Windows)
            import threading
            import queue
            
            result_queue = queue.Queue()
            
            def geocode_worker():
                try:
                    lat, lon = self.geocodificar_endereco(endereco)
                    result_queue.put((lat, lon, None))
                except Exception as e:
                    result_queue.put((None, None, str(e)))
            
            # Iniciar thread com timeout de 15 segundos
            thread = threading.Thread(target=geocode_worker)
            thread.daemon = True
            thread.start()
            thread.join(timeout=15)
            
            if thread.is_alive():
                self.logger.error(f"[GEO] TIMEOUT (15s) - Geocodificacao cancelada")
                return endereco, None, None, None
            
            # Obter resultado
            try:
                lat, lon, error = result_queue.get_nowait()
                if error:
                    self.logger.error(f"[GEO] Erro na geocodificacao: {error[:50]}...")
                    return endereco, None, None, None
            except queue.Empty:
                self.logger.error(f"[GEO] Nenhum resultado da geocodificacao")
                return endereco, None, None, None
            
            if not lat or not lon:
                return endereco, None, None, None
            
            distancia = self.calcular_distancia(
                self.lat_referencia, self.lon_referencia, lat, lon
            )
            
            self.logger.info(f"[GEO] Distancia calculada: {distancia}km")
            return endereco, lat, lon, distancia
            
        except Exception as e:
            self.logger.error(f"[GEO] Erro inesperado: {str(e)[:100]}...")
            return endereco, None, None, None