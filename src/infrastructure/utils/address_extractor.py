"""
Extrator e formatador de endereços - Responsabilidade única
"""
import re
from typing import Optional
from ...domain.models.address_model import AddressModel


class AddressExtractor:
    """Extrai e formata endereços do HTML para geolocalização"""

    # Padrões de endereço completo
    ADDRESS_PATTERNS = [
        r'(\d{5}-?\d{3})[^a-zA-Z]*([^,\n]*(?:rua|av\.|avenida|alameda)[^,\n]+[^,\n]*são\s*paulo[^,\n]*)',
        r'(?:rua|av\.|avenida|alameda|travessa)\s+[^,\n]+,?\s*\d+[^,\n]*[^,\n]*(?:são\s*paulo|sp)',
        r'(?:endereço|address)[:=]\s*([^<\n]+(?:rua|av\.|avenida)[^<\n]+(?:são\s*paulo|sp))',
        r'(av\.?\s*[^\d]*\d+[^,]*(?:vila|jardim|bairro)[^,]*são\s*paulo)',
        r'aria-label[^>]*([^,]+,\s*\d+[^,]*[^,]*são\s*paulo[^,]*)',
        r'([^\n]*(?:rua|av\.|avenida)[^\n]*\d+[^\n]*são\s*paulo[^\n]*)',
    ]

    # Padrões de cidade/bairro
    CITY_PATTERNS = [
        r'(?:moema|vila\s+mariana|pinheiros|itaim|jardins|centro|liberdade|bela\s+vista)',
        r'(?:campinas|guarulhos|santo\s+andré|são\s+bernardo|osasco|barueri)',
        r'(?:cidade|localização)[:=]\s*([^,<\n]+)',
        r'são\s+paulo\s*[-,]\s*sp'
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
        numero = cls._extract_number(html_lower)
        bairro = cls._extract_neighborhood(html_lower)
        cep = cls._extract_cep(html_lower)
        
        return AddressModel(
            logradouro=logradouro,
            numero=numero,
            bairro=bairro,
            cidade="São Paulo",
            estado="SP",
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
    def _extract_number(cls, html_lower: str) -> str:
        """Extrai número"""
        patterns = [
            r'(?:rua|avenida)[^\d]*?(\d{1,5})(?:\s|,|$)',
            r'número[^\d]*(\d{1,5})'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_lower)
            if matches:
                return matches[0]
        return ""
    
    @classmethod
    def _extract_neighborhood(cls, html_lower: str) -> str:
        """Extrai bairro"""
        neighborhoods = [
            'moema', 'vila mariana', 'pinheiros', 'itaim', 'jardins',
            'centro', 'liberdade', 'bela vista', 'consolacao', 'higienopolis'
        ]
        
        for neighborhood in neighborhoods:
            if neighborhood in html_lower:
                return neighborhood.title()
        return ""
    
    @classmethod
    def _extract_cep(cls, html_lower: str) -> str:
        """Extrai CEP"""
        pattern = r'(\d{5}-?\d{3})'
        matches = re.findall(pattern, html_lower)
        if matches:
            return matches[0]
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
                return f"{cidade.strip()}, São Paulo, SP"
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

        # Garante São Paulo no final
        if not any(sp in endereco.lower() for sp in ['são paulo', 'sp']):
            endereco += ', São Paulo, SP'

        return endereco.strip()

    @classmethod
    def _validate_address(cls, endereco: str) -> bool:
        """Valida se endereço é válido"""
        if len(endereco) < 15:
            return False

        endereco_lower = endereco.lower()

        tem_logradouro = any(tipo in endereco_lower for tipo in cls.STREET_TYPES)
        tem_sao_paulo = any(sp in endereco_lower for sp in ['são paulo', 'sp'])
        tem_muitos_numeros = len(re.findall(r'\d{4,}', endereco)) > 1

        return tem_logradouro and tem_sao_paulo and not tem_muitos_numeros

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

        # Garante Brasil no final para geocodificação
        if 'brasil' not in endereco.lower():
            if 'sp' not in endereco.lower():
                endereco += ', São Paulo, SP'
            endereco += ', Brasil'

        return endereco
