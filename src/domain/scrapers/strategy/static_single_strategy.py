"""
Static Single Page Strategy - Estratégia para sites estáticos simples
"""
from ..models import ExtractionResult
from ..classify.site_type_enum import SiteType
from ..extract.extraction_chain import ExtractionChain
from .base_strategy import BaseStrategy


class StaticSinglePageStrategy(BaseStrategy):
    """
    Estratégia para STATIC_SINGLE_PAGE

    Fluxo:
    1. FastPath (CSS)
    2. Se falhar → Regex
    3. Normalizar
    4. FIM

    SEM navegação adicional
    """

    def __init__(self):
        super().__init__()
        self.site_type = SiteType.STATIC_SINGLE_PAGE
        self.chain = ExtractionChain()

    def extract(self, html: str, url: str, fetcher=None) -> ExtractionResult:
        """
        Extração simples e direta

        Não usa SmartPath (navegação) pois é página única
        """
        # Usar extraction chain (FastPath → Regex)
        # SmartPath será pulado automaticamente pois não tem fetcher
        result = self.chain.extract(html, self.site_type)

        # Adicionar URL ao resultado
        if result.success:
            result.url = url
            result.domain = self._extract_domain(url)

        return result

    def _extract_domain(self, url: str) -> str:
        """Extrai domínio da URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return url
