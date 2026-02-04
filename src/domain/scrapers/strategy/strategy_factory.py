"""
Strategy Factory - Factory para criar estratégias por tipo de site
"""
from ..classify.site_type_enum import SiteType
from .base_strategy import BaseStrategy
from .static_single_strategy import StaticSinglePageStrategy
from .corporate_multi_strategy import CorporateMultiPageStrategy
from .business_directory_strategy import BusinessDirectoryStrategy
from .franchise_strategy import FranchiseStrategy
from .pdf_first_strategy import PdfFirstStrategy
from .unknown_strategy import UnknownStrategy


class StrategyFactory:
    """
    Factory Pattern para criar estratégias

    Mapeia cada SiteType para sua estratégia correspondente
    """

    # Mapeamento de tipos para estratégias
    _strategies = {
        SiteType.STATIC_SINGLE_PAGE: StaticSinglePageStrategy,
        SiteType.CORPORATE_MULTI_PAGE: CorporateMultiPageStrategy,
        SiteType.BUSINESS_DIRECTORY: BusinessDirectoryStrategy,
        SiteType.FRANCHISE: FranchiseStrategy,
        SiteType.PDF_FIRST_SITE: PdfFirstStrategy,
        SiteType.UNKNOWN: UnknownStrategy,

        # Tipos sem estratégia específica ainda (usar fallback)
        SiteType.B2B_PORTAL: BusinessDirectoryStrategy,  # Similar a directory
        SiteType.SEARCH_RESULTS: UnknownStrategy,        # Não processar
        SiteType.MARKETPLACE: UnknownStrategy,           # Não processar
        SiteType.BLOG_ARTICLE: StaticSinglePageStrategy, # Tratar como static
        SiteType.SOCIAL_PROFILE: UnknownStrategy,        # Não processar
    }

    @classmethod
    def create(cls, site_type: SiteType) -> BaseStrategy:
        """
        Cria estratégia apropriada para o tipo de site

        Args:
            site_type: Tipo de site classificado

        Returns:
            BaseStrategy: Instância da estratégia
        """
        strategy_class = cls._strategies.get(site_type, UnknownStrategy)
        return strategy_class()

    @classmethod
    def get_available_strategies(cls) -> dict:
        """
        Retorna mapeamento completo de estratégias

        Returns:
            dict: {SiteType: StrategyClass}
        """
        return cls._strategies.copy()
