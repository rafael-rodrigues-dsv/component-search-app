"""
Budget Manager - Controla limites de tempo, páginas e requisições
"""
import time
from typing import Dict
from ..classify.site_type_enum import SiteType


class BudgetManager:
    """Gerencia budgets de tempo, páginas e requisições"""

    # Budgets padrão por tipo de site
    DEFAULT_BUDGETS = {
        SiteType.STATIC_SINGLE_PAGE: {
            'max_time_seconds': 2,
            'max_pages': 1,
            'max_requests': 1
        },
        SiteType.CORPORATE_MULTI_PAGE: {
            'max_time_seconds': 5,
            'max_pages': 3,
            'max_requests': 4
        },
        SiteType.BUSINESS_DIRECTORY: {
            'max_time_seconds': 15,
            'max_pages': 10,
            'max_requests': 12
        },
        SiteType.B2B_PORTAL: {
            'max_time_seconds': 15,
            'max_pages': 10,
            'max_requests': 12
        },
        SiteType.FRANCHISE: {
            'max_time_seconds': 8,
            'max_pages': 5,
            'max_requests': 6
        },
        SiteType.PDF_FIRST_SITE: {
            'max_time_seconds': 3,
            'max_pages': 1,
            'max_requests': 1
        },
        SiteType.SEARCH_RESULTS: {
            'max_time_seconds': 8,
            'max_pages': 5,
            'max_requests': 6
        },
        SiteType.UNKNOWN: {
            'max_time_seconds': 2,
            'max_pages': 1,
            'max_requests': 1
        }
    }

    def __init__(self, site_type: SiteType, custom_budgets: Dict = None):
        """
        Inicializa budget manager

        Args:
            site_type: Tipo de site
            custom_budgets: Budgets customizados (opcional, sobrescreve padrões)
        """
        # Usar custom budgets se fornecido, senão usar padrão
        if custom_budgets and site_type.name.lower().replace('_', '') in custom_budgets:
            self.budget = custom_budgets[site_type.name.lower().replace('_', '')]
        else:
            self.budget = self.DEFAULT_BUDGETS.get(
                site_type,
                self.DEFAULT_BUDGETS[SiteType.UNKNOWN]
            )

        self.site_type = site_type
        self.start_time = time.time()
        self.pages_visited = 0
        self.requests_made = 0

    def can_continue(self) -> bool:
        """
        Verifica se ainda há budget disponível

        Returns:
            bool: True se pode continuar, False se budget esgotado
        """
        elapsed = time.time() - self.start_time

        if elapsed > self.budget['max_time_seconds']:
            return False

        if self.pages_visited >= self.budget['max_pages']:
            return False

        if self.requests_made >= self.budget['max_requests']:
            return False

        return True

    def record_page_visit(self):
        """Registra visita a uma página"""
        self.pages_visited += 1

    def record_request(self):
        """Registra uma requisição HTTP"""
        self.requests_made += 1

    def elapsed_ms(self) -> int:
        """Retorna tempo decorrido em milissegundos"""
        return int((time.time() - self.start_time) * 1000)

    def elapsed_seconds(self) -> float:
        """Retorna tempo decorrido em segundos"""
        return time.time() - self.start_time

    def remaining_time_seconds(self) -> float:
        """Retorna tempo restante em segundos"""
        return max(0, self.budget['max_time_seconds'] - self.elapsed_seconds())

    def remaining_pages(self) -> int:
        """Retorna páginas restantes"""
        return max(0, self.budget['max_pages'] - self.pages_visited)

    def remaining_requests(self) -> int:
        """Retorna requisições restantes"""
        return max(0, self.budget['max_requests'] - self.requests_made)

    def get_status(self) -> dict:
        """Retorna status atual do budget"""
        return {
            'site_type': self.site_type.name,
            'elapsed_ms': self.elapsed_ms(),
            'pages_visited': self.pages_visited,
            'requests_made': self.requests_made,
            'can_continue': self.can_continue(),
            'budget': self.budget
        }
