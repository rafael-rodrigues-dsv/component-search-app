"""
Protocols para scrapers
"""
from typing import Protocol, List
from ..models.company_model import CompanyModel


class ScraperProtocol(Protocol):
    """Protocol que define interface para scrapers"""
    
    def search(self, query: str) -> bool:
        """Executa busca por termo"""
        ...
    
    def get_result_links(self, blacklist: List[str]) -> List[str]:
        """Obtém links dos resultados"""
        ...
    
    def extract_company_data(self, url: str, max_emails: int) -> CompanyModel:
        """Extrai dados da empresa"""
        ...
    
    def go_to_next_page(self) -> bool:
        """Vai para próxima página (opcional)"""
        ...