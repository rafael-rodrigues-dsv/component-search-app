"""
Regex Extractor - Fallback usando regex contextual
"""
import re
from typing import List, Set, Optional
from ..models import ExtractionResult
from ..classify.site_type_enum import SiteType, ExtractionPath


class RegexExtractor:
    """
    Fallback: regex em escopo limitado + validação rigorosa

    Usado quando FastPath e SmartPath falharam
    """

    # Regex otimizadas
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        re.IGNORECASE
    )

    PHONE_BR_PATTERN = re.compile(
        r'(?:\+55\s*)?(?:\(?\d{2}\)?\s*)?9?\d{4,5}[-\s]?\d{4}',
        re.IGNORECASE
    )

    # Blacklist de domínios
    BLACKLIST_DOMAINS = {
        'example.com', 'test.com', 'domain.com', 'email.com',
        'sentry.io', 'googletagmanager.com', 'facebook.com',
        'google.com', 'youtube.com', 'twitter.com', 'instagram.com',
        'linkedin.com', 'w3.org', 'schema.org', 'wix.com',
        'wordpress.com', 'blogger.com'
    }

    # Prefixos suspeitos
    BLACKLIST_PREFIXES = {
        'test@', 'demo@', 'noreply@', 'no-reply@',
        'privacy@', 'terms@', 'support@', 'help@',
        'info@example', 'contact@example'
    }

    def __init__(self):
        pass

    def try_extract(self, html: str, site_type: SiteType) -> ExtractionResult:
        """
        Aplica regex em escopo reduzido do HTML

        Otimizações:
        1. Limitar HTML a primeiros 50KB
        2. Remover scripts/styles antes
        3. Aplicar regex por chunks (não no HTML inteiro)
        4. Validação rigorosa de cada match

        Args:
            html: HTML da página
            site_type: Tipo de site

        Returns:
            ExtractionResult: Resultado da extração
        """
        try:
            # Limitar escopo (performance)
            clean_html = self._clean_html(html[:50000])

            # Extrair em chunks para evitar regex global
            emails = self._extract_emails_validated(clean_html)
            phones = self._extract_phones_validated(clean_html)

            if emails or phones:
                return ExtractionResult.success_result(
                    emails=list(emails),
                    phones=list(phones),
                    address=None,
                    path=ExtractionPath.REGEX_PATH
                )

            return ExtractionResult.failure()

        except Exception as e:
            return ExtractionResult.failure()

    def _clean_html(self, html: str) -> str:
        """
        Limpa HTML removendo scripts, styles e tags

        Returns:
            Texto limpo
        """
        # Remover scripts
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)

        # Remover styles
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

        # Remover comentários HTML
        html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)

        # Remover tags (deixar apenas texto)
        html = re.sub(r'<[^>]+>', ' ', html)

        # Normalizar espaços
        html = re.sub(r'\s+', ' ', html)

        return html

    def _extract_emails_validated(self, text: str) -> Set[str]:
        """
        Extrai e valida emails rigorosamente

        Returns:
            Set de emails válidos
        """
        potential = self.EMAIL_PATTERN.findall(text)
        validated = set()

        for email in potential:
            email = email.lower().strip()

            # Validações
            if not self._is_valid_email(email):
                continue

            validated.add(email)

            # EARLY EXIT: limite de emails
            if len(validated) >= 5:
                break

        return validated

    def _extract_phones_validated(self, text: str) -> Set[str]:
        """
        Extrai e valida telefones rigorosamente

        Returns:
            Set de telefones válidos
        """
        potential = self.PHONE_BR_PATTERN.findall(text)
        validated = set()

        for phone in potential:
            phone = phone.strip()

            # Validações
            if not self._is_valid_phone(phone):
                continue

            validated.add(phone)

            # EARLY EXIT: limite de telefones
            if len(validated) >= 3:
                break

        return validated

    def _is_valid_email(self, email: str) -> bool:
        """
        Validação rigorosa de email

        Returns:
            bool: True se válido
        """
        # Tamanho
        if len(email) < 6 or len(email) > 100:
            return False

        # Estrutura básica
        if email.count('@') != 1:
            return False

        try:
            local, domain = email.split('@')

            # Validar domínio
            if '.' not in domain:
                return False

            # Blacklist de domínios
            if domain in self.BLACKLIST_DOMAINS:
                return False

            # Blacklist de prefixos
            if any(email.startswith(prefix) for prefix in self.BLACKLIST_PREFIXES):
                return False

            # Validar caracteres
            if '..' in email or email.startswith('.') or email.endswith('.'):
                return False

            return True

        except:
            return False

    def _is_valid_phone(self, phone: str) -> bool:
        """
        Validação rigorosa de telefone brasileiro

        Returns:
            bool: True se válido
        """
        # Limpar
        clean = re.sub(r'[^\d]', '', phone)

        # Tamanho (10 ou 11 dígitos)
        if len(clean) not in [10, 11]:
            return False

        # Validar DDD (11-99)
        if len(clean) >= 2:
            ddd = int(clean[:2])
            if ddd < 11 or ddd > 99:
                return False

        # Se tem 11 dígitos, o 3º deve ser 9 (celular)
        if len(clean) == 11 and clean[2] != '9':
            return False

        # Não pode ser todos dígitos iguais
        if len(set(clean)) < 3:
            return False

        return True
