"""
Business Directory Strategy - Estratégia para diretórios de empresas
"""
from typing import List
from bs4 import BeautifulSoup
from ..models import ExtractionResult
from ..classify.site_type_enum import SiteType
from ..extract.extraction_chain import ExtractionChain
from .base_strategy import BaseStrategy


class BusinessDirectoryStrategy(BaseStrategy):
    """
    Estratégia para BUSINESS_DIRECTORY

    Fluxo:
    1. Detectar padrão de repetição
    2. Extrair links de empresas (máx N)
    3. Para cada link:
       a. Tentar FastPath
       b. Se falhar → SmartPath
       c. Se sucesso → EARLY EXIT
    4. Retornar lista de empresas

    Budget: MAX_COMPANIES = 10
    """

    MAX_COMPANIES = 10  # Limite de empresas a processar

    def __init__(self):
        super().__init__()
        self.site_type = SiteType.BUSINESS_DIRECTORY
        self.chain = ExtractionChain()

    def extract(self, html: str, url: str, fetcher=None) -> ExtractionResult:
        """
        Extrai dados de DIRETÓRIO

        IMPORTANTE: Este tipo NÃO deve extrair dados da página principal,
        apenas identificar que é um diretório e abortar.

        Extração de empresas individuais seria feito em outra camada.
        """
        # Diretórios não devem ser processados diretamente
        # Apenas retornar failure para indicar que é uma lista

        result = ExtractionResult.failure()
        result.url = url
        result.domain = self._extract_domain(url)

        # Marcar como diretório nos metadados
        return result

    def extract_company_links(self, html: str, url: str) -> List[str]:
        """
        Extrai links de empresas do diretório

        Este método seria usado se quiséssemos processar cada empresa
        """
        try:
            soup = BeautifulSoup(html, 'lxml')

            # Detectar padrão de repetição para encontrar links de empresas
            company_links = self._find_company_links(soup, url)

            return company_links[:self.MAX_COMPANIES]
        except:
            return []

    def _find_company_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Encontra links de empresas baseado em padrões repetitivos

        Returns:
            Lista de URLs de empresas
        """
        links = []

        # Buscar links repetidos (mesmo padrão de classe)
        all_links = soup.find_all('a', href=True)

        # Agrupar por classe para detectar padrão
        class_groups = {}
        for link in all_links:
            classes = ' '.join(link.get('class', []))
            if classes:
                if classes not in class_groups:
                    class_groups[classes] = []
                class_groups[classes].append(link.get('href'))

        # Pegar grupo com mais links (provavelmente empresas)
        if class_groups:
            most_common_class = max(class_groups.items(), key=lambda x: len(x[1]))
            links = most_common_class[1]

        # Resolver URLs relativas
        resolved_links = []
        for href in links:
            full_url = self._resolve_url(href, base_url)
            if full_url and full_url != base_url:  # Não incluir link para própria página
                resolved_links.append(full_url)

        return resolved_links

    def _resolve_url(self, href: str, base_url: str) -> str:
        """Resolve URL relativa"""
        try:
            from urllib.parse import urljoin, urlparse

            if href.startswith('http'):
                parsed_base = urlparse(base_url)
                parsed_href = urlparse(href)
                if parsed_base.netloc == parsed_href.netloc:
                    return href
                return None

            return urljoin(base_url, href)
        except:
            return None

    def _extract_domain(self, url: str) -> str:
        """Extrai domínio da URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return url
