"""
Extrator e formatador de endereços - Responsabilidade única
"""
import re
from typing import Optional

from ...domain.models.address_model import AddressModel


class AddressExtractor:
    """Extrai e formata endereços do HTML para geolocalização"""

    # Padrões de endereço completo (genéricos)
    ADDRESS_PATTERNS = [
        r'(\d{5}-?\d{3})[^a-zA-Z]*([^,\n]*(?:rua|av\.|avenida|alameda)[^,\n]+)',
        r'(?:rua|av\.|avenida|alameda|travessa)\s+[^,\n]+,?\s*\d+[^,\n]*',
        r'(?:endereço|address)[:=]\s*([^<\n]+(?:rua|av\.|avenida)[^<\n]+)',
        r'(av\.?\s*[^\d]*\d+[^,]*(?:vila|jardim|bairro)[^,]*)',
        r'aria-label[^>]*([^,]+,\s*\d+[^,]*)',
        r'([^\n]*(?:rua|av\.|avenida)[^\n]*\d+[^\n]*)',
    ]

    # Padrões de cidade/bairro (genéricos)
    CITY_PATTERNS = [
        r'(vila\s+[a-záéíóú\s]{3,25})',
        r'(jardim\s+[a-záéíóú\s]{3,25})',
        r'(?:cidade|localização)[:=]\s*([^,<\n]+)',
        r'([a-záéíóú\s]{3,25})\s*[-,]\s*[a-z]{2}'
    ]

    # Ruídos técnicos para remoção
    NOISE_PATTERNS = [
        r'aria-label\S*', r'title\S*', r'amp\S*', r'zoom\d+',
        r'quot\S*', r'url\S*', r'http\S*', r'maps\.google\S*',
        r'section\S*', r'main_block\S*', r'action\S*', r'address\S*',
        r'adv_address\S*', r'id\S*', r'copy_lo\S*', r'log\S*'
    ]

    # Tipos de logradouro válidos
    STREET_TYPES = ['rua', 'av.', 'avenida', 'alameda', 'travessa', 'praça']

    @classmethod
    def extract_from_html(cls, html_content: str) -> Optional[AddressModel]:
        """Extrai endereço estruturado do HTML (otimizado)"""
        if not html_content:
            return None

        # Limitar HTML para performance (primeiros 50KB)
        if len(html_content) > 50000:
            html_content = html_content[:50000]

        # Tentar extrair endereço estruturado
        address = cls._extract_structured_address(html_content)
        if address and address.is_valid():
            return address

        return None
    
    @classmethod
    def _extract_structured_address(cls, html_content: str) -> Optional[AddressModel]:
        """Extrai endereço em formato estruturado"""
        html_lower = html_content.lower()
        
        # Buscar componentes do endereço
        logradouro = cls._extract_street(html_lower)
        numero, complemento = cls._extract_number_and_complement(html_lower)
        bairro = cls._extract_neighborhood(html_lower)
        cep = cls._extract_cep(html_lower)
        
        # Extrair cidade dinamicamente
        cidade = cls._extract_city(html_lower)
        estado = cls._extract_state(html_lower)
        
        return AddressModel(
            logradouro=logradouro,
            numero=numero,
            complemento=complemento,
            bairro=bairro,
            cidade=cidade,
            estado=estado,
            cep=cep
        )
    
    @classmethod
    def _extract_street(cls, html_lower: str) -> str:
        """Extrai logradouro completo (tipo + nome)"""
        patterns = [
            r'((?:rua|av\.|avenida|alameda|travessa|praça)\s+[^,\n\d]{3,40})',
            r'endereço[^>]*([^,\n]*(?:rua|avenida|alameda)[^,\n]{5,50})',
            r'((?:r\.|av\.)\s+[^,\n\d]{3,30})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_lower)
            if matches:
                street = matches[0].strip()
                # Limpar e normalizar
                street = re.sub(r'\s+', ' ', street)
                street = street.replace('av.', 'avenida').replace('r.', 'rua')
                if len(street) > 3:
                    return street.title()
        return ""
    
    @classmethod
    def _extract_number_and_complement(cls, html_lower: str) -> tuple[str, str]:
        """Extrai número e complemento separadamente"""
        patterns = [
            # Padrão: número + complemento (123 Apto 45, 456-A, 789 Sala 12)
            r'(?:rua|avenida)[^\d]*?(\d{1,5})\s*([a-zA-Z].*?)(?:\s|,|$)',
            r'número[^\d]*(\d{1,5})\s*([a-zA-Z].*?)(?:\s|,|$)',
            # Padrão: apenas número
            r'(?:rua|avenida)[^\d]*?(\d{1,5})(?:\s|,|$)',
            r'número[^\d]*(\d{1,5})(?:\s|,|$)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_lower)
            if matches:
                match = matches[0]
                if isinstance(match, tuple) and len(match) == 2:
                    numero, complemento = match
                    # Limpar complemento
                    complemento = cls._clean_complement(complemento)
                    return numero.strip(), complemento
                else:
                    # Apenas número encontrado
                    return str(match).strip(), ""
        return "", ""
    
    @classmethod
    def _clean_complement(cls, complemento: str) -> str:
        """Limpa e normaliza complemento"""
        if not complemento:
            return ""
            
        # Remover caracteres especiais e normalizar
        complemento = re.sub(r'[^a-zA-Z0-9\s]', ' ', complemento)
        complemento = re.sub(r'\s+', ' ', complemento).strip()
        
        # Limitar tamanho
        if len(complemento) > 50:
            complemento = complemento[:50]
            
        return complemento.title()
    
    @classmethod
    def _extract_neighborhood(cls, html_lower: str) -> str:
        """Extrai bairro (busca dinâmica)"""
        # Padrões genéricos de bairro
        patterns = [
            r'(?:bairro|distrito)\s+([a-záéíóú\s]{3,30})',
            r'(vila\s+[a-záéíóú\s]{3,25})',
            r'(jardim\s+[a-záéíóú\s]{3,25})',
            r'(centro)(?:\s|,|$)',
            r'([a-záéíóú\s]{3,25})\s*,\s*(?:são\s*paulo|sp|campinas|sorocaba)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_lower)
            if matches:
                bairro = matches[0].strip()
                if len(bairro) >= 3 and not any(char.isdigit() for char in bairro):
                    return bairro.title()
        return ""
    
    @classmethod
    def _extract_city(cls, html_lower: str) -> str:
        """Extrai cidade dinamicamente - TODAS as cidades do Brasil"""
        patterns = [
            r'(?:cidade|city)\s*[:=]\s*([a-záéíóúàâãêôõç\s]{3,40})',
            # Padrão genérico para qualquer cidade brasileira com UF
            r'([a-záéíóúàâãêôõç\s]{3,35})\s*,\s*(?:ac|al|ap|am|ba|ce|df|es|go|ma|mt|ms|mg|pa|pb|pr|pe|pi|rj|rn|rs|ro|rr|sc|sp|se|to)\b',
            r'([a-záéíóúàâãêôõç\s]{3,35})\s*-\s*(?:ac|al|ap|am|ba|ce|df|es|go|ma|mt|ms|mg|pa|pb|pr|pe|pi|rj|rn|rs|ro|rr|sc|sp|se|to)\b',
            # Cidades conhecidas (mais restritivo)
            r'\b(são\s+paulo|rio\s+de\s+janeiro|belo\s+horizonte|salvador|brasília|fortaleza|manaus|curitiba|recife|porto\s+alegre|goiânia|belém|guarulhos|campinas|são\s+luís|são\s+gonçalo|maceió|duque\s+de\s+caxias|natal|teresina|campo\s+grande|nova\s+iguaçu|são\s+bernardo\s+do\s+campo|joão\s+pessoa|santo\s+andré|osasco|jaboatão\s+dos\s+guararapes|são\s+josé\s+dos\s+campos|ribeirão\s+preto|uberlândia|sorocaba|contagem|aracaju|feira\s+de\s+santana|cuiabá|joinville|aparecida\s+de\s+goiânia|londrina|ananindeua|porto\s+velho|serra|niterói|caxias\s+do\s+sul|mauá|são\s+joão\s+de\s+meriti|campos\s+dos\s+goytacazes|vila\s+velha|florianópolis|santos|mogi\s+das\s+cruzes|diadema|jundiá\s+|carapicuíba|piracicaba|bauru|itaquaquecetuba|são\s+vicente|franca|guarujá|taubaté|praia\s+grande|limeira|suzano|taboão\s+da\s+serra|sumaré|são\s+carlos|marília|indaiatuba|americana|araraquara|jacareí|itu|rio\s+claro|araçatuba|são\s+josé\s+do\s+rio\s+preto|presidente\s+prudente|guarulhos|campinas|sorocaba)\b'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_lower)
            if matches:
                cidade = matches[0].strip()
                if len(cidade) >= 3 and cls._is_valid_city_name(cidade):
                    return cidade.title()
        return ""  # Sem fallback fixo
    
    @classmethod
    def _extract_state(cls, html_lower: str) -> str:
        """Extrai estado dinamicamente - TODOS os estados do Brasil"""
        patterns = [
            # Todos os 26 estados + DF
            r'\b(ac|al|ap|am|ba|ce|df|es|go|ma|mt|ms|mg|pa|pb|pr|pe|pi|rj|rn|rs|ro|rr|sc|sp|se|to)\b',
            r'(?:estado|state|uf)\s*[:=]\s*([a-z]{2})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_lower)
            if matches:
                return matches[0].upper()
        return ""  # Sem fallback fixo
    
    @classmethod
    def _is_valid_city_name(cls, city_name: str) -> bool:
        """Valida se o nome é realmente uma cidade e não termo de negócio"""
        city_lower = city_name.lower()
        
        # Filtrar termos de negócio que não são cidades
        business_terms = [
            'elevador', 'manutenção', 'empresa', 'serviço', 'instalação',
            'modernização', 'assistência', 'técnica', 'central', 'comercial',
            'industrial', 'residencial', 'predial', 'condomínio', 'edifício',
            'ltda', 'me', 'eireli', 'sa', 's.a', 'inc', 'corp', 'group',
            # Nomes de empresas comuns que aparecem como cidade
            'crea', 'blue', 'gradient', 'shrink', 'slide', 'lim', 'do lim',
            'elevadores', 'tecnologia', 'sistemas', 'soluções', 'engenharia',
            'construção', 'arquitetura', 'design', 'consultoria', 'logística'
        ]
        
        # Se contém termos de negócio, não é cidade
        if any(term in city_lower for term in business_terms):
            return False
            
        # Se tem números, provavelmente não é cidade
        if any(char.isdigit() for char in city_name):
            return False
            
        return True
    
    @classmethod
    def _extract_cep(cls, html_lower: str) -> str:
        """Extrai CEP e remove traços"""
        pattern = r'(\d{5}-?\d{3})'
        matches = re.findall(pattern, html_lower)
        if matches:
            # Remove traços do CEP
            return matches[0].replace('-', '')
        return ""

    @classmethod
    def _extract_complete_address(cls, html_content: str) -> Optional[str]:
        """Extrai endereço completo"""
        html_lower = html_content.lower()

        for pattern in cls.ADDRESS_PATTERNS:
            matches = re.findall(pattern, html_lower, re.IGNORECASE | re.MULTILINE)
            if matches:
                for match in matches:
                    endereco = cls._process_match(match)
                    if endereco and cls._validate_address(endereco):
                        return endereco
        return None

    @classmethod
    def _extract_partial_address(cls, html_content: str) -> Optional[str]:
        """Extrai cidade/bairro"""
        html_lower = html_content.lower()

        for pattern in cls.CITY_PATTERNS:
            matches = re.findall(pattern, html_lower, re.IGNORECASE)
            if matches:
                cidade = matches[0] if isinstance(matches[0], str) else matches[0]
                return f"{cidade.strip()}"
        return None

    @classmethod
    def _process_match(cls, match) -> str:
        """Processa match de regex"""
        if isinstance(match, tuple):
            endereco = ' '.join([m for m in match if m]).strip()
        else:
            endereco = match.strip()

        return cls._clean_address(endereco)

    @classmethod
    def _clean_address(cls, endereco: str) -> str:
        """Limpa endereço removendo ruídos"""
        # Remove tags HTML
        endereco = re.sub(r'<[^>]+>', '', endereco)

        # Remove ruídos técnicos
        for ruido in cls.NOISE_PATTERNS:
            endereco = re.sub(ruido, '', endereco, flags=re.IGNORECASE)

        # Remove caracteres especiais exceto vírgulas, pontos e hífens
        endereco = re.sub(r'[^\w\s,.\-]', ' ', endereco)

        # Remove IDs numéricos longos
        endereco = re.sub(r'\s+\d{4,}\s*$', '', endereco)

        # Normaliza espaços
        endereco = ' '.join(endereco.split())

        # Não força cidade específica - mantém dinâmico

        return endereco.strip()

    @classmethod
    def _validate_address(cls, endereco: str) -> bool:
        """Valida se endereço é válido"""
        if len(endereco) < 15:
            return False

        endereco_lower = endereco.lower()

        tem_logradouro = any(tipo in endereco_lower for tipo in cls.STREET_TYPES)
        tem_cidade = len([word for word in endereco_lower.split() if len(word) > 2]) > 3
        tem_muitos_numeros = len(re.findall(r'\d{4,}', endereco)) > 1

        return tem_logradouro and tem_cidade and not tem_muitos_numeros

    @classmethod
    def _format_address(cls, endereco: str) -> str:
        """Formata endereço para geolocalização"""
        # Remove ruídos específicos
        endereco = re.sub(r'\s*-\s*nbsp\s*', ' ', endereco)
        endereco = re.sub(r'\d+cep\s*\d{5}-?\d{3}\s*-?', ' ', endereco, flags=re.IGNORECASE)
        endereco = re.sub(r'cep\s*\d{5}-?\d{3}', ' ', endereco, flags=re.IGNORECASE)
        endereco = re.sub(r'\s+sp\s+sp\s*', ' SP ', endereco, flags=re.IGNORECASE)

        # Normalizar abreviações
        endereco = re.sub(r'\bav\.?\s+', 'avenida ', endereco, flags=re.IGNORECASE)
        endereco = re.sub(r'\br\.?\s+', 'rua ', endereco, flags=re.IGNORECASE)

        # Normaliza espaços
        endereco = re.sub(r'\s+', ' ', endereco).strip()

        # Garante Brasil no final para geocodificação (sem forçar cidade)
        if 'brasil' not in endereco.lower():
            endereco += ', Brasil'

        return endereco
