"""
Base Strategy - Interface para estratégias de extração
"""
from abc import ABC, abstractmethod
from typing import Optional
from ..models import ExtractionResult
from ..classify.site_type_enum import SiteType


class BaseStrategy(ABC):
    """
    Interface base para estratégias de extração por tipo de site

    Cada tipo de site tem seu próprio comportamento de extração
    """

    def __init__(self):
        self.site_type: Optional[SiteType] = None

    @abstractmethod
    def extract(self, html: str, url: str, fetcher=None) -> ExtractionResult:
        """
        Extrai dados do site usando estratégia específica

        Args:
            html: HTML da página principal
            url: URL da página
            fetcher: HttpFetcher para navegação adicional (opcional)

        Returns:
            ExtractionResult: Dados extraídos
        """
        pass

    def get_site_type(self) -> SiteType:
        """Retorna tipo de site que esta estratégia trata"""
        return self.site_type
