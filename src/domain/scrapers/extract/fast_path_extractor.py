"""
Fast Path Extractor - Extração ultra-rápida via CSS selectors
"""
import re
from typing import List, Optional, Set
from bs4 import BeautifulSoup
from ..models import ExtractionResult
from ..classify.site_type_enum import SiteType, ExtractionPath
from .context_selectors import ContextSelectors


class FastPathExtractor:
    """
    Extração rápida via CSS selectors em regiões específicas

    Objetivo: Resolver 80% dos casos em < 100ms
    """

    # Regex para validação básica
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'\(?\d{2}\)?\s*9?\d{4,5}[-\s]?\d{4}')

    # Domínios suspeitos para filtrar
    SUSPICIOUS_DOMAINS = {
        'example.com', 'test.com', 'domain.com', 'email.com',
        'sentry.io', 'googletagmanager.com', 'facebook.com',
        'google.com', 'youtube.com', 'twitter.com', 'instagram.com',
        'linkedin.com', 'w3.org', 'schema.org'
    }

    def __init__(self):
        self.selectors = ContextSelectors()

    def try_extract(self, html: str, site_type: SiteType) -> ExtractionResult:
        """
        Tenta extração rápida limitando escopo ao DOM relevante

        Estratégia:
        1. Parsear HTML (BeautifulSoup)
        2. Buscar em header/footer primeiro
        3. Aplicar CSS selectors contextuais
        4. Validar dados encontrados
        5. Se válido → SUCCESS (early exit)

        Args:
            html: HTML da página
            site_type: Tipo de site (pode influenciar estratégia)

        Returns:
            ExtractionResult: Resultado da extração
        """
        try:
            # Parsear HTML
            soup = BeautifulSoup(html, 'lxml')

            # ESCOPO LIMITADO: apenas regiões relevantes
            contexts = self._get_priority_contexts(soup)

            # Extrair dados
            emails = self._extract_emails_from_contexts(contexts, soup)
            phones = self._extract_phones_from_contexts(contexts, soup)
            address = self._extract_address_from_contexts(contexts, soup)

            # Validação: tem dados mínimos?
            if self._has_valid_data(emails, phones):
                return ExtractionResult.success_result(
                    emails=list(emails),
                    phones=list(phones),
                    address=address,
                    path=ExtractionPath.FAST_PATH
                )

            return ExtractionResult.failure()

        except Exception as e:
            # Falha silenciosa, próximo extractor tentará
            return ExtractionResult.failure()

    def _get_priority_contexts(self, soup: BeautifulSoup) -> List:
        """
        Extrai regiões prioritárias do HTML

        Returns:
            List de elementos BeautifulSoup
        """
        contexts = []

        # Buscar regiões prioritárias
        for selector in self.selectors.get_priority_regions():
            try:
                element = soup.select_one(selector)
                if element:
                    contexts.append(element)
            except:
                continue

        # Se não encontrou nenhuma região, usa body inteiro (fallback)
        if not contexts:
            body = soup.find('body')
            if body:
                contexts.append(body)

        return contexts

    def _extract_emails_from_contexts(self, contexts: List, soup: BeautifulSoup) -> Set[str]:
        """
        Extrai emails dos contextos prioritários

        Returns:
            Set de emails válidos
        """
        emails = set()

        # Tentar seletores CSS primeiro (mais rápido)
        for selector in self.selectors.get_email_selectors():
            try:
                elements = soup.select(selector)
                for elem in elements[:10]:  # Limitar a 10 por seletor
                    email = self._extract_email_from_element(elem)
                    if email and self._is_valid_email(email):
                        emails.add(email.lower())
                        if len(emails) >= 5:  # Early exit
                            return emails
            except:
                continue

        # Buscar em contextos prioritários (fallback)
        if len(emails) < 3:
            for context in contexts[:3]:  # Limitar a 3 contextos
                text = context.get_text() if context else ""
                found = self.EMAIL_PATTERN.findall(text)

                for email in found[:10]:
                    if self._is_valid_email(email):
                        emails.add(email.lower())
                        if len(emails) >= 5:
                            return emails

        return emails

    def _extract_phones_from_contexts(self, contexts: List, soup: BeautifulSoup) -> Set[str]:
        """
        Extrai telefones dos contextos prioritários

        Returns:
            Set de telefones válidos
        """
        phones = set()

        # Tentar seletores CSS primeiro
        for selector in self.selectors.get_phone_selectors():
            try:
                elements = soup.select(selector)
                for elem in elements[:10]:
                    phone = self._extract_phone_from_element(elem)
                    if phone and self._is_valid_phone(phone):
                        phones.add(phone)
                        if len(phones) >= 3:
                            return phones
            except:
                continue

        # Buscar em contextos prioritários (fallback)
        if len(phones) < 2:
            for context in contexts[:3]:
                text = context.get_text() if context else ""
                found = self.PHONE_PATTERN.findall(text)

                for phone in found[:10]:
                    if self._is_valid_phone(phone):
                        phones.add(phone)
                        if len(phones) >= 3:
                            return phones

        return phones

    def _extract_address_from_contexts(self, contexts: List, soup: BeautifulSoup) -> Optional[str]:
        """
        Extrai endereço dos contextos prioritários

        Returns:
            String do endereço ou None
        """
        # Tentar seletores CSS primeiro
        for selector in self.selectors.get_address_selectors():
            try:
                element = soup.select_one(selector)
                if element:
                    address = element.get_text(strip=True)
                    if address and len(address) > 10:
                        return address[:200]  # Limitar tamanho
            except:
                continue

        return None

    def _extract_email_from_element(self, element) -> Optional[str]:
        """Extrai email de um elemento HTML"""
        try:
            # Tentar href primeiro (links mailto)
            href = element.get('href', '')
            if href.startswith('mailto:'):
                email = href.replace('mailto:', '').split('?')[0]
                return email.strip()

            # Tentar data attributes
            email = element.get('data-email', '') or element.get('data-contact-email', '')
            if email:
                return email.strip()

            # Tentar texto do elemento
            text = element.get_text(strip=True)
            match = self.EMAIL_PATTERN.search(text)
            if match:
                return match.group(0)
        except:
            pass

        return None

    def _extract_phone_from_element(self, element) -> Optional[str]:
        """Extrai telefone de um elemento HTML"""
        try:
            # Tentar href primeiro (links tel)
            href = element.get('href', '')
            if href.startswith('tel:'):
                phone = href.replace('tel:', '').strip()
                return phone

            # Tentar data attributes
            phone = element.get('data-phone', '') or element.get('data-tel', '')
            if phone:
                return phone.strip()

            # Tentar texto do elemento
            text = element.get_text(strip=True)
            match = self.PHONE_PATTERN.search(text)
            if match:
                return match.group(0)
        except:
            pass

        return None

    def _is_valid_email(self, email: str) -> bool:
        """Valida email"""
        if not email or len(email) < 6 or len(email) > 100:
            return False

        if '@' not in email or '.' not in email.split('@')[1]:
            return False

        # Filtrar domínios suspeitos
        try:
            domain = email.split('@')[1].lower()
            if domain in self.SUSPICIOUS_DOMAINS:
                return False
        except:
            return False

        return True

    def _is_valid_phone(self, phone: str) -> bool:
        """Valida telefone brasileiro"""
        # Limpar
        clean = re.sub(r'[^\d]', '', phone)

        # Telefone brasileiro tem 10 ou 11 dígitos
        if len(clean) not in [10, 11]:
            return False

        # Validar DDD (primeiros 2 dígitos)
        if len(clean) >= 2:
            ddd = int(clean[:2])
            if ddd < 11 or ddd > 99:
                return False

        return True

    def _has_valid_data(self, emails: Set[str], phones: Set[str]) -> bool:
        """Verifica se tem dados mínimos válidos"""
        return len(emails) > 0 or len(phones) > 0
