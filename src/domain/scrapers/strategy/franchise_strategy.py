"""
Franchise Strategy - Estratégia para franquias/múltiplas unidades
"""
from ..models import ExtractionResult
from ..classify.site_type_enum import SiteType
from ..extract.extraction_chain import ExtractionChain
from .base_strategy import BaseStrategy


class FranchiseStrategy(BaseStrategy):
    """
    Estratégia para FRANCHISE

    Franquias têm múltiplas unidades, cada uma com seus próprios dados

    Fluxo:
    1. Identificar se é página de listagem de unidades
    2. Se for listagem: extrair links de unidades
    3. Se for unidade individual: extrair dados normalmente
    4. Cada unidade = entidade independente
    """

    def __init__(self):
        super().__init__()
        self.site_type = SiteType.FRANCHISE
        self.chain = ExtractionChain()

    def extract(self, html: str, url: str, fetcher=None) -> ExtractionResult:
        """
        Extração de franquia

        Se é página de listagem, não extrair dados (retornar failure)
        Se é página de unidade específica, extrair normalmente
        """
        # Verificar se é página de listagem de unidades
        if self._is_units_listing(html):
            # É listagem, não extrair dados
            result = ExtractionResult.failure()
            result.url = url
            result.domain = self._extract_domain(url)
            return result

        # É unidade específica, extrair normalmente
        result = self.chain.extract(html, self.site_type, fetcher, url)

        if result.success:
            result.url = url
            result.domain = self._extract_domain(url)

        return result

    def _is_units_listing(self, html: str) -> bool:
        """
        Verifica se é página de listagem de unidades

        Returns:
            bool: True se é listagem
        """
        html_lower = html.lower()

        # Palavras-chave que indicam listagem
        listing_keywords = [
            'nossas unidades',
            'nossas lojas',
            'todas as unidades',
            'encontre uma unidade',
            'onde estamos',
            'nossas filiais'
        ]

        # Se encontrar múltiplas palavras-chave, é listagem
        count = sum(1 for keyword in listing_keywords if keyword in html_lower)

        return count >= 2

    def _extract_domain(self, url: str) -> str:
        """Extrai domínio da URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return url
