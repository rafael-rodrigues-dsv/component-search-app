"""
Entidade SearchTerm - Representa um termo de busca
"""
from dataclasses import dataclass

@dataclass
class SearchTermModel:
    """Entidade Termo de Busca"""
    query: str
    location: str
    category: str
    pages: int