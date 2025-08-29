"""
Camada de Domínio - Regras de negócio para coleta de e-mails
"""
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List

import tldextract
from config.settings import SUSPICIOUS_EMAIL_DOMAINS

from ..models.company_model import CompanyModel
from ..models.search_term_model import SearchTermModel

# Constantes para validação
MAX_EMAIL_LENGTH = 100
MIN_PHONE_DIGITS = 10
MAX_PHONE_DIGITS = 11
MIN_DDD = 11
MAX_DDD = 99
MIN_UNIQUE_DIGITS_PHONE = 3
CELLULAR_THIRD_DIGIT = '9'


class EmailCollectorInterface(ABC):
    """Interface para coleta de e-mails"""
    
    @abstractmethod
    def collect_emails(self, terms: List[SearchTermModel]) -> List[CompanyModel]:
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
        if len(email) > MAX_EMAIL_LENGTH:
            return False
        
        # Rejeita e-mails com caracteres suspeitos ou múltiplos e-mails
        if any(char in email for char in ['@1.5x', '@2x', '@3x', ';', '|', '\\', '/', '?', '#', '%20', '%', '&']):
            return False
        
        # Rejeita e-mails que começam com caracteres suspeitos
        if email.startswith(('%20', '%', '&', ' ', '\t', '\n')):
            return False
        
        # Rejeita se contém múltiplos @ (múltiplos e-mails concatenados)
        if email.count('@') != 1:
            return False
        
        # Rejeita se começa ou termina com caracteres suspeitos
        if email.startswith((';', '|', ',', ' ', '%')) or email.endswith((';', '|', ',', ' ', '%')):
            return False
        
        # Rejeita domínios suspeitos
        domain = email.split('@')[1] if '@' in email else ''
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
        phone = re.sub(r'[^0-9]', '', phone.strip())
        
        # Telefone deve ter exatamente 10 ou 11 dígitos
        if len(phone) not in [MIN_PHONE_DIGITS, MAX_PHONE_DIGITS]:
            return False
        
        # Não pode começar com 0
        if phone.startswith('0'):
            return False
        
        # DDD deve ser válido (11-99)
        ddd = phone[:2]
        if not (MIN_DDD <= int(ddd) <= MAX_DDD):
            return False
        
        # Se tem 11 dígitos, o terceiro deve ser 9 (celular)
        if len(phone) == MAX_PHONE_DIGITS and phone[2] != CELLULAR_THIRD_DIGIT:
            return False
        
        # Rejeita números repetitivos ou sequenciais
        if len(set(phone)) <= MIN_UNIQUE_DIGITS_PHONE:  # Muitos dígitos iguais
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
        clean_phone = re.sub(r'[^0-9]', '', phone.strip())
        
        if len(clean_phone) == MAX_PHONE_DIGITS:  # Celular com 9
            return f"({clean_phone[:2]}) {clean_phone[2:7]}-{clean_phone[7:]}"
        elif len(clean_phone) == MIN_PHONE_DIGITS:  # Fixo
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


