"""
Advanced Extraction Service - Extração usando REGEX PURO
"""
import re
from typing import List, Optional, Tuple
class AdvancedExtractionService:
    def __init__(self):
        self.blacklist_domains = {
            'example.com', 'test.com', 'domain.com', 'email.com',
            'sentry.io', 'googletagmanager.com', 'facebook.com',
            'google.com', 'youtube.com', 'twitter.com', 'instagram.com'
        }
        self.blacklist_prefixes = {
            'test@', 'demo@', 'noreply@', 'no-reply@',
            'privacy@', 'terms@', 'support@', 'help@'
        }
    def extract_emails(self, html: str, max_emails: int = 3) -> List[str]:
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        potential_emails = re.findall(pattern, html)
        valid = []
        for email in potential_emails:
            email = email.lower()
            try:
                domain = email.split('@')[1]
            except:
                continue
            if domain in self.blacklist_domains:
                continue
            if any(email.startswith(prefix) for prefix in self.blacklist_prefixes):
                continue
            if email.count('@') != 1:
                continue
            if '.' not in domain:
                continue
            if len(email) < 6:
                continue
            if email not in valid:
                valid.append(email)
                if len(valid) >= max_emails:
                    break
        return valid
    def extract_phones(self, html: str, max_phones: int = 2) -> List[str]:
        patterns = [
            r'\(?\d{2}\)?\s*9?\d{4,5}[-\s]?\d{4}',
            r'\+55\s*\(?\d{2}\)?\s*9?\d{4,5}[-\s]?\d{4}'
        ]
        phones = set()
        for pattern in patterns:
            found = re.findall(pattern, html)
            for phone in found:
                clean = re.sub(r'[^\d]', '', phone)
                if len(clean) in [10, 11]:
                    phones.add(phone.strip())
                    if len(phones) >= max_phones:
                        return list(phones)
        return list(phones)
    def extract_address(self, html: str) -> Optional[str]:
        try:
            from src.infrastructure.utils.address_extractor import AddressExtractor
            address_obj = AddressExtractor.extract_from_html(html)
            if address_obj and address_obj.is_valid():
                return address_obj.to_full_address()
        except:
            pass
        try:
            patterns = [
                r'(?:Rua|Av\.|Avenida|Travessa)\s+[^,\n]+,\s*\d+[^,\n]*',
                r'[^,\n]+,\s*\d+[^,\n]*\s*-\s*CEP:?\s*\d{5}-?\d{3}'
            ]
            for pattern in patterns:
                matches = re.findall(pattern, html, re.IGNORECASE)
                if matches:
                    longest = max(matches, key=len)
                    if len(longest) > 15:
                        return longest.strip()
        except:
            pass
        return None
    def extract_all(self, html: str, max_emails: int = 3, max_phones: int = 2) -> Tuple[List[str], List[str], Optional[str]]:
        emails = self.extract_emails(html, max_emails)
        phones = self.extract_phones(html, max_phones)
        address = self.extract_address(html)
        return emails, phones, address
_service = None
def get_advanced_extraction_service() -> AdvancedExtractionService:
    global _service
    if _service is None:
        _service = AdvancedExtractionService()
    return _service
