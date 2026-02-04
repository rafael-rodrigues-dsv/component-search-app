"""
Unknown Strategy - Estratégia fallback para sites não identificados
"""
from ..models import ExtractionResult
from ..classify.site_type_enum import SiteType
from ..extract.extraction_chain import ExtractionChain
from .base_strategy import BaseStrategy


class UnknownStrategy(BaseStrategy):
    """
    Estratégia para UNKNOWN

    Tentativa mínima e conservadora:
    1. FastPath
    2. Regex
    3. Se falhar, marcar como descartado
    """

    def __init__(self):
        super().__init__()
        self.site_type = SiteType.UNKNOWN
        self.chain = ExtractionChain()

    def extract(self, html: str, url: str, fetcher=None) -> ExtractionResult:
        """
        Tentativa conservadora de extração

        Não usa SmartPath (navegação) para evitar perder tempo
        """
        # Extraction chain sem SmartPath (não passa fetcher)
        result = self.chain.extract(html, self.site_type)

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
