"""
Corporate Multi Page Strategy - Estratégia para sites corporativos multi-página
"""
from ..models import ExtractionResult
from ..classify.site_type_enum import SiteType
from ..extract.extraction_chain import ExtractionChain
from .base_strategy import BaseStrategy


class CorporateMultiPageStrategy(BaseStrategy):
    """
    Estratégia para CORPORATE_MULTI_PAGE

    Fluxo:
    1. FastPath na home
    2. Se falhar → SmartPath (navegar /contato, /sobre)
    3. Limitar a MAX_PAGES = 3
    4. Normalizar
    """

    def __init__(self):
        super().__init__()
        self.site_type = SiteType.CORPORATE_MULTI_PAGE
        self.chain = ExtractionChain()

    def extract(self, html: str, url: str, fetcher=None) -> ExtractionResult:
        """
        Extração com possível navegação para páginas de contato

        Se fetcher disponível, usa SmartPath para tentar /contato
        """
        # Usar extraction chain completo (inclui SmartPath se tiver fetcher)
        result = self.chain.extract(html, self.site_type, fetcher, url)

        # Adicionar metadados
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
