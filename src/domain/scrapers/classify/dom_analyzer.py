"""
DOM Analyzer - Análise de estrutura DOM para classificação
"""
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from ..models import DOMMetrics


class DOMAnalyzer:
    """
    Analisa estrutura DOM para auxiliar na classificação de sites

    Métricas extraídas:
    - Repetição de padrões (indica lista/diretório)
    - Densidade de links
    - Complexidade de navegação
    - Paginação
    - Profundidade estrutural
    """

    # Padrões que indicam paginação
    PAGINATION_PATTERNS = [
        r'pagination',
        r'pager',
        r'page-numbers',
        r'next-page',
        r'prev-page',
        r'próxima',
        r'anterior'
    ]

    # Links de navegação comum em sites corporativos
    NAVIGATION_KEYWORDS = [
        'contato', 'contact',
        'sobre', 'about',
        'serviços', 'services',
        'produtos', 'products',
        'unidades', 'locations',
        'fale-conosco'
    ]

    def analyze(self, html: str) -> DOMMetrics:
        """
        Analisa HTML e retorna métricas DOM

        Args:
            html: HTML da página

        Returns:
            DOMMetrics: Métricas calculadas
        """
        try:
            # Limitar HTML para performance (100KB)
            if len(html) > 100000:
                html = html[:100000]

            soup = BeautifulSoup(html, 'lxml')

            return DOMMetrics(
                repetition_score=self._calculate_repetition(soup),
                link_density=self._calculate_link_density(soup),
                navigation_complexity=self._count_nav_links(soup),
                has_pagination=self._has_pagination(soup),
                structural_depth=self._calculate_depth(soup),
                total_tags=len(soup.find_all()),
                total_links=len(soup.find_all('a'))
            )

        except Exception as e:
            # Retornar métricas vazias em caso de erro
            return DOMMetrics()

    def _calculate_repetition(self, soup: BeautifulSoup) -> float:
        """
        Calcula score de repetição (0-1)

        Lógica:
        - Conta classes CSS repetidas
        - Analisa tags com mesma estrutura
        - Retorna score normalizado

        Score alto = provável lista/diretório

        Returns:
            float: Score de 0 a 1
        """
        class_counts = {}

        # Contar repetições de classes
        for tag in soup.find_all(class_=True):
            classes = tag.get('class', [])
            for cls in classes:
                # Ignorar classes genéricas
                if cls.lower() not in ['container', 'row', 'col', 'hidden', 'show']:
                    class_counts[cls] = class_counts.get(cls, 0) + 1

        if not class_counts:
            return 0.0

        # Pegar máximo de repetições
        max_repetition = max(class_counts.values())

        # Normalizar: 10+ repetições = score alto (provável lista)
        # 20+ repetições = score máximo (muito provável lista)
        score = min(max_repetition / 20.0, 1.0)

        return round(score, 2)

    def _calculate_link_density(self, soup: BeautifulSoup) -> float:
        """
        Calcula densidade de links (links / total_tags)

        Densidade alta = provável diretório/portal

        Returns:
            float: Densidade de 0 a 1
        """
        total_tags = len(soup.find_all())
        total_links = len(soup.find_all('a'))

        if total_tags == 0:
            return 0.0

        density = total_links / total_tags

        return round(min(density, 1.0), 2)

    def _count_nav_links(self, soup: BeautifulSoup) -> int:
        """
        Conta links de navegação relevantes

        Links para /contato, /sobre, etc = site corporativo

        Returns:
            int: Número de links de navegação
        """
        links = soup.find_all('a', href=True)
        count = 0

        for link in links:
            href = link.get('href', '').lower()
            text = link.get_text().lower().strip()

            # Verificar se href ou texto contém palavras-chave
            for keyword in self.NAVIGATION_KEYWORDS:
                if keyword in href or keyword in text:
                    count += 1
                    break  # Não contar o mesmo link múltiplas vezes

        return count

    def _has_pagination(self, soup: BeautifulSoup) -> bool:
        """
        Detecta presença de paginação

        Paginação = provável lista/diretório

        Returns:
            bool: True se tem paginação
        """
        # Buscar por classes/ids relacionados a paginação
        for pattern in self.PAGINATION_PATTERNS:
            # Buscar em classes
            if soup.find(class_=re.compile(pattern, re.IGNORECASE)):
                return True

            # Buscar em IDs
            if soup.find(id=re.compile(pattern, re.IGNORECASE)):
                return True

            # Buscar em texto de links
            links = soup.find_all('a', string=re.compile(pattern, re.IGNORECASE))
            if links:
                return True

        # Buscar por símbolos comuns de paginação
        pagination_symbols = ['›', '»', '«', '‹', 'next', 'prev', 'anterior', 'próxima']
        for symbol in pagination_symbols:
            if soup.find('a', string=re.compile(symbol, re.IGNORECASE)):
                return True

        return False

    def _calculate_depth(self, soup: BeautifulSoup) -> int:
        """
        Calcula profundidade estrutural média da árvore DOM

        Profundidade alta = estrutura complexa

        Returns:
            int: Profundidade média
        """
        def get_depth(element, current_depth=0):
            """Recursivamente calcula profundidade"""
            if not element.children:
                return current_depth

            max_child_depth = current_depth
            for child in element.children:
                if child.name:  # Ignorar strings de texto
                    child_depth = get_depth(child, current_depth + 1)
                    max_child_depth = max(max_child_depth, child_depth)

            return max_child_depth

        try:
            body = soup.find('body')
            if body:
                return get_depth(body)
            return 0
        except:
            return 0

    def get_summary(self, metrics: DOMMetrics) -> Dict[str, str]:
        """
        Gera resumo textual das métricas

        Args:
            metrics: Métricas DOM

        Returns:
            Dict com interpretações
        """
        summary = {}

        # Repetição
        if metrics.repetition_score > 0.5:
            summary['repetition'] = "ALTA - Provável lista/diretório"
        elif metrics.repetition_score > 0.3:
            summary['repetition'] = "MÉDIA - Pode ter alguns itens repetidos"
        else:
            summary['repetition'] = "BAIXA - Estrutura única"

        # Densidade de links
        if metrics.link_density > 0.3:
            summary['link_density'] = "ALTA - Provável diretório/portal"
        elif metrics.link_density > 0.15:
            summary['link_density'] = "MÉDIA - Site normal"
        else:
            summary['link_density'] = "BAIXA - Pouco conteúdo linkado"

        # Navegação
        if metrics.navigation_complexity > 5:
            summary['navigation'] = "ALTA - Site corporativo multi-página"
        elif metrics.navigation_complexity > 2:
            summary['navigation'] = "MÉDIA - Alguma navegação"
        else:
            summary['navigation'] = "BAIXA - Site simples"

        # Paginação
        summary['pagination'] = "SIM" if metrics.has_pagination else "NÃO"

        return summary
