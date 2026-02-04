"""
Site Type Enum - Classificação de tipos de site
"""
from enum import Enum, auto


class SiteType(Enum):
    """Tipos de site para classificação determinística"""

    STATIC_SINGLE_PAGE = auto()      # Site estático, 1 página
    CORPORATE_MULTI_PAGE = auto()    # Site corporativo, múltiplas páginas
    BUSINESS_DIRECTORY = auto()      # Diretório/lista de empresas
    B2B_PORTAL = auto()              # Portal B2B (fornecedores)
    FRANCHISE = auto()               # Franquias/múltiplas unidades
    BLOG_ARTICLE = auto()            # Artigo de blog
    SEARCH_RESULTS = auto()          # Página de resultados de busca
    MARKETPLACE = auto()             # Marketplace
    SOCIAL_PROFILE = auto()          # Perfil social (LinkedIn, etc)
    PDF_FIRST_SITE = auto()          # Site que é basicamente um PDF
    UNKNOWN = auto()                 # Não identificado


class DetectionConfidence(Enum):
    """Nível de confiança na classificação"""
    HIGH = auto()     # > 80% certeza
    MEDIUM = auto()   # 50-80% certeza
    LOW = auto()      # < 50% certeza


class ExtractionPath(Enum):
    """Caminho de extração utilizado"""
    FAST_PATH = auto()    # CSS selectors contextuais (< 100ms)
    SMART_PATH = auto()   # Navegação limitada (< 1s)
    REGEX_PATH = auto()   # Fallback regex
    FAILED = auto()       # Nenhum teve sucesso
