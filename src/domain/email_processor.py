"""
Camada de Domínio - Regras de negócio para coleta de e-mails
"""
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List

import tldextract


@dataclass
class Company:
    """Entidade Empresa"""
    name: str
    emails: str  # String com e-mails separados por ;
    domain: str
    url: str
    search_term: str = ""
    address: str = ""
    phone: str = ""


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
        
        # Verifica formato básico
        if not re.match(r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$", email):
            return False
        
        # Rejeita e-mails muito longos (provavelmente lixo)
        if len(email) > 100:
            return False
        
        # Rejeita e-mails com caracteres suspeitos ou múltiplos e-mails
        if any(char in email for char in ['@1.5x', '@2x', '@3x', ';', '|', '\\', '/', '?', '#']):
            return False
        
        # Rejeita se contém múltiplos @ (múltiplos e-mails concatenados)
        if email.count('@') != 1:
            return False
        
        # Rejeita se começa ou termina com caracteres suspeitos
        if email.startswith((';', '|', ',', ' ')) or email.endswith((';', '|', ',', ' ')):
            return False
        
        # Rejeita domínios suspeitos
        domain = email.split('@')[1] if '@' in email else ''
        from config.settings import SUSPICIOUS_EMAIL_DOMAINS
        if any(susp in domain for susp in SUSPICIOUS_EMAIL_DOMAINS):
            return False
        
        # Rejeita e-mails com palavras suspeitas
        bad_bits = [
            "example", "exemplo", "teste", "test", "email@", "@email", 
            "no-reply", "noreply", "spam", "featured", "@1.", "@2.", "@3.",
            "jpg", "png", "gif", "webp", "svg"
        ]
        return not any(b in email for b in bad_bits)
    
    def validate_and_join_emails(self, email_list: List[str]) -> str:
        """Valida cada e-mail e junta em string separada por ;"""
        valid_emails = []
        seen = set()
        
        for email in email_list:
            clean_email = email.strip().lower()
            if clean_email and clean_email not in seen and self.is_valid_email(clean_email):
                valid_emails.append(clean_email)
                seen.add(clean_email)
        
        result = ';'.join(valid_emails)
        return result + ';' if result else ''
    
    def is_valid_phone(self, phone: str) -> bool:
        """Valida formato de telefone brasileiro"""
        import re
        phone = re.sub(r'[^0-9]', '', phone.strip())
        
        # Telefone deve ter exatamente 10 ou 11 dígitos
        if len(phone) not in [10, 11]:
            return False
        
        # Não pode começar com 0
        if phone.startswith('0'):
            return False
        
        # DDD deve ser válido (11-99)
        ddd = phone[:2]
        if not (11 <= int(ddd) <= 99):
            return False
        
        # Se tem 11 dígitos, o terceiro deve ser 9 (celular)
        if len(phone) == 11 and phone[2] != '9':
            return False
        
        # Rejeita números repetitivos ou sequenciais
        if len(set(phone)) <= 3:  # Muitos dígitos iguais
            return False
        
        # Rejeita padrões suspeitos
        suspicious_patterns = [
            '1234567890', '0987654321', '1111111111', '2222222222',
            '9999999999', '0000000000', '1234512345'
        ]
        if phone in suspicious_patterns:
            return False
            
        return True
    
    def format_phone(self, phone: str) -> str:
        """Formata telefone com máscara brasileira"""
        import re
        clean_phone = re.sub(r'[^0-9]', '', phone.strip())
        
        if len(clean_phone) == 11:  # Celular com 9
            return f"({clean_phone[:2]}) {clean_phone[2:7]}-{clean_phone[7:]}"
        elif len(clean_phone) == 10:  # Fixo
            return f"({clean_phone[:2]}) {clean_phone[2:6]}-{clean_phone[6:]}"
        else:
            return clean_phone
    
    def validate_and_join_phones(self, phone_list: list) -> str:
        """Valida cada telefone e junta em string separada por ;"""
        valid_phones = []
        seen = set()
        
        for phone in phone_list:
            clean_phone = phone.strip()
            if clean_phone and clean_phone not in seen and self.is_valid_phone(clean_phone):
                formatted_phone = self.format_phone(clean_phone)
                valid_phones.append(formatted_phone)
                seen.add(clean_phone)
        
        result = ';'.join(valid_phones)
        return result + ';' if result else ''
    
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