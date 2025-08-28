"""
Fábrica de termos de busca
"""
from typing import List

from config.settings import *
from ..models.search_term_model import SearchTermModel


class SearchTermFactory:
    """Cria termos de busca baseado na configuração"""
    
    @staticmethod
    def create_search_terms() -> List[SearchTermModel]:
        """Cria lista de termos baseado no modo (teste/produção)"""
        search_terms = []
        
        if IS_TEST_MODE:
            print("[INFO] Modo TESTE ativado via settings.py")
            for base in BASE_TESTES:
                search_terms.append(f"{base} {CIDADE_BASE} capital")
        else:
            print("[INFO] Modo PRODUÇÃO - processamento completo")
            # Capital
            for base in BASE_BUSCA:
                search_terms.append(f"{base} {CIDADE_BASE} capital")

            # Zonas
            for base in BASE_BUSCA:
                for zona in BASE_ZONAS:
                    search_terms.append(f"{base} {zona} {CIDADE_BASE}")

            # Bairros
            for base in BASE_BUSCA:
                for bairro in BASE_BAIRROS:
                    search_terms.append(f"{base} {bairro} {CIDADE_BASE}")

            # Interior
            for base in BASE_BUSCA:
                for cidade in CIDADES_INTERIOR:
                    search_terms.append(f"{base} {cidade} {UF_BASE}")

        # Converte para objetos SearchTerm
        return [SearchTermModel(query=term, location=UF_BASE, category=CATEGORIA_BASE, pages=10) for term in search_terms]