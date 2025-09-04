"""
Entidade Company - Representa uma empresa coletada
"""
from dataclasses import dataclass


@dataclass
class CompanyModel:
    """Entidade Empresa"""
    name: str
    emails: str  # String com e-mails separados por ;
    domain: str
    url: str
    search_term: str = ""
    address: str = ""
    phone: str = ""
    html_content: str = ""
