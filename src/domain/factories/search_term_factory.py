"""
Fábrica de termos de busca
"""
from typing import List

from src.infrastructure.config.config_manager import ConfigManager
from src.application.services.search_term_service import SearchTermService
from ..models.search_term_model import SearchTermModel


class SearchTermFactory:
    """Cria termos de busca baseado na configuração"""

    _config = ConfigManager()
    IS_TEST_MODE = _config.is_test_mode
    _term_service = SearchTermService()

    @classmethod
    def create_search_terms(cls) -> List[SearchTermModel]:
        """Cria lista de termos baseado no modo (teste/produção)

        Implementação:
        - Tenta obter termos ativos do banco (TB_BASE_BUSCA)
        - Se não houver termos no banco, usa as constantes BASE_TESTES / BASE_BUSCA como fallback
        - Retorna objetos SearchTermModel com campos mínimos preenchidos
        """
        # Primeiro: tentar obter termos do banco (ativos)
        try:
            rows = cls._term_service.get_active_terms(is_test=cls.IS_TEST_MODE)
            if rows:
                print(f"[INFO] Obtidos {len(rows)} termos ativos do banco")
                search_terms = [r.get('TERMO_BUSCA') or r.get('termo') for r in rows if (r.get('TERMO_BUSCA') or r.get('termo'))]
            else:
                raise Exception("Sem termos no banco - fallback")
        except Exception:
            # Fallback simplificado: usar BASE_TESTES / BASE_BUSCA (strings simples)
            if cls.IS_TEST_MODE:
                print("[INFO] Modo TESTE ativado (fallback para BASE_TESTES)")
                from config.settings import BASE_TESTES  # Importar apenas quando necessário
                base_list = BASE_TESTES
            else:
                print("[INFO] Modo PRODUÇÃO - processamento completo (fallback para BASE_BUSCA)")
                from config.settings import BASE_BUSCA  # Importar apenas quando necessário
                base_list = BASE_BUSCA

            # Garantir que base_list seja uma lista de strings
            search_terms = [str(t).strip() for t in base_list if t]

        # Converter para objetos SearchTermModel (preencher location/category com valores padrão)
        return [SearchTermModel(query=term, location='', category='base', pages=10) for term in search_terms]
