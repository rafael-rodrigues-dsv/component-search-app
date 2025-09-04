"""
Fábrica de termos de busca
"""
from typing import List

from config.settings import *
from src.infrastructure.config.config_manager import ConfigManager
from ..models.search_term_model import SearchTermModel


class SearchTermFactory:
    """Cria termos de busca baseado na configuração"""

    _config = ConfigManager()
    IS_TEST_MODE = _config.is_test_mode

    @classmethod
    def create_search_terms(cls) -> List[SearchTermModel]:
        """Cria lista de termos baseado no modo (teste/produção)"""
        if cls.IS_TEST_MODE:
            print("[INFO] Modo TESTE ativado")
            search_terms = [f"{base} {CIDADE_BASE} capital" for base in BASE_TESTES]
        else:
            print("[INFO] Modo PRODUÇÃO - processamento completo")
            search_terms = (
                # Capital
                    [f"{base} {CIDADE_BASE} capital" for base in BASE_BUSCA] +
                    # Zonas
                    [f"{base} {zona} {CIDADE_BASE}" for base in BASE_BUSCA for zona in BASE_ZONAS] +
                    # Bairros
                    [f"{base} {bairro} {CIDADE_BASE}" for base in BASE_BUSCA for bairro in BASE_BAIRROS] +
                    # Interior
                    [f"{base} {cidade} {UF_BASE}" for base in BASE_BUSCA for cidade in CIDADES_INTERIOR]
            )

        # Converte para objetos SearchTerm
        return [SearchTermModel(query=term, location=UF_BASE, category=CATEGORIA_BASE, pages=10) for term in
                search_terms]
