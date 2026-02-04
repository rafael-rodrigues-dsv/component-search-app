"""
Context Selectors - Seletores CSS contextuais para extração rápida
"""
from typing import List, Dict


class ContextSelectors:
    """Seletores CSS organizados por contexto para extração otimizada"""

    # Seletores para EMAIL em contextos específicos
    EMAIL_SELECTORS = [
        # Links mailto
        "footer a[href^='mailto:']",
        "header a[href^='mailto:']",
        ".contact a[href^='mailto:']",
        ".contact-info a[href^='mailto:']",
        ".footer a[href^='mailto:']",
        "#contact a[href^='mailto:']",
        "#footer a[href^='mailto:']",

        # Classes comuns
        "a.email",
        ".email a",
        "span.email",
        ".contact-email",
        ".email-address",

        # Schema.org
        "[itemtype*='ContactPoint'] a[href^='mailto:']",
        "[itemprop='email']",

        # Data attributes
        "[data-email]",
        "[data-contact-email]",
    ]

    # Seletores para TELEFONE
    PHONE_SELECTORS = [
        # Links tel
        "a[href^='tel:']",
        "footer a[href^='tel:']",
        "header a[href^='tel:']",
        ".contact a[href^='tel:']",

        # Classes comuns
        ".phone",
        ".telefone",
        ".tel",
        ".contact-phone",
        ".phone-number",
        "span.phone",

        # Schema.org
        "[itemtype*='ContactPoint'] span[itemprop='telephone']",
        "[itemprop='telephone']",

        # Data attributes
        "[data-phone]",
        "[data-tel]",
    ]

    # Seletores para ENDEREÇO
    ADDRESS_SELECTORS = [
        # Tags semânticas
        "address",

        # Schema.org
        "[itemtype*='PostalAddress']",
        "[itemprop='address']",

        # Classes comuns
        ".address",
        ".endereco",
        ".location",
        ".contact-address",

        # Footer/Header comum
        "#footer .location",
        ".footer .address",
        ".contact .address",
    ]

    # Regiões prioritárias para busca (ordem de prioridade)
    PRIORITY_REGIONS = [
        "footer",
        "header",
        ".contact",
        ".contact-info",
        "#contact",
        ".footer",
        "#footer",
        ".header",
        "#header",
        "aside",
    ]

    @classmethod
    def get_email_selectors(cls) -> List[str]:
        """Retorna lista de seletores CSS para email"""
        return cls.EMAIL_SELECTORS

    @classmethod
    def get_phone_selectors(cls) -> List[str]:
        """Retorna lista de seletores CSS para telefone"""
        return cls.PHONE_SELECTORS

    @classmethod
    def get_address_selectors(cls) -> List[str]:
        """Retorna lista de seletores CSS para endereço"""
        return cls.ADDRESS_SELECTORS

    @classmethod
    def get_priority_regions(cls) -> List[str]:
        """Retorna lista de regiões prioritárias"""
        return cls.PRIORITY_REGIONS

    @classmethod
    def get_all_selectors(cls) -> Dict[str, List[str]]:
        """Retorna todos os seletores organizados"""
        return {
            'email': cls.EMAIL_SELECTORS,
            'phone': cls.PHONE_SELECTORS,
            'address': cls.ADDRESS_SELECTORS,
            'regions': cls.PRIORITY_REGIONS
        }
