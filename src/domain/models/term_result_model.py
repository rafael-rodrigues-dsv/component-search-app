"""
Modelo para resultado do processamento de um termo de busca
"""
from dataclasses import dataclass
from typing import List


@dataclass
class TermResultModel:
    """Resultado do processamento de um termo de busca"""
    saved_count: int
    processed_count: int
    success: bool
    term_query: str
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
