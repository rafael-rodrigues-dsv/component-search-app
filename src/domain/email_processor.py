"""
Camada de Domínio - Regras de negócio para coleta de e-mails
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import re
import tldextract
from datetime import datetime


@dataclass
class Company:
    """Entidade Empresa"""
    name: str
    emails: List[str]
    domain: str
    url: str
    search_term: str = ""
    address: str = ""


@dataclass
class SearchTerm:
    """Entidade Termo de Busca"""
    query: str
    location: str
    category: str
    pages: int


class EmailCollectorInterface(ABC):
    """Interface para coleta de e-mails"""
    
    @abstractmethod
    def collect_emails(self, terms: List[SearchTerm]) -> List[Company]:
        pass


class EmailValidationService:
    """Serviço de validação de e-mails"""
    
    def is_valid_email(self, email: str) -> bool:
        """Valida formato e conteúdo do e-mail"""
        email = email.strip().lower()
        if not re.match(r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$", email):
            return False
        bad_bits = ["example", "exemplo", "teste", "email@", "@email", "no-reply", "noreply", "spam"]
        return not any(b in email for b in bad_bits)
    
    def extract_domain_from_url(self, url: str) -> str:
        """Extrai domínio da URL"""
        ext = tldextract.extract(url)
        if ext.domain and ext.suffix:
            return f"{ext.domain}.{ext.suffix}"
        return url


class WorkingHoursService:
    """Serviço de horário de trabalho"""
    
    def __init__(self, start_hour: int, end_hour: int):
        self.start_hour = start_hour
        self.end_hour = end_hour
    
    def is_working_time(self) -> bool:
        """Verifica se está no horário de trabalho"""
        current_hour = datetime.now().hour
        return self.start_hour <= current_hour < self.end_hour


class SearchTermBuilder:
    """Construtor de termos de busca"""
    
    def build_elevator_terms(self, base_terms: List[str], zonas: List[str], 
                           bairros: List[str], cidades: List[str]) -> List[SearchTerm]:
        """Constrói termos para elevadores"""
        terms = []
        
        # Capital geral
        for base in base_terms:
            terms.append(SearchTerm(f"{base} São Paulo capital", "capital", "elevadores", 80))
        
        # Por zonas
        for base in base_terms:
            for zona in zonas:
                terms.append(SearchTerm(f"{base} {zona} São Paulo", "zona", "elevadores", 25))
        
        # Por bairros
        for base in base_terms:
            for bairro in bairros:
                terms.append(SearchTerm(f"{base} {bairro} São Paulo", "bairro", "elevadores", 12))
        
        # Interior
        for base in base_terms:
            for cidade in cidades:
                terms.append(SearchTerm(f"{base} {cidade} SP", "interior", "elevadores", 20))
        
        return terms