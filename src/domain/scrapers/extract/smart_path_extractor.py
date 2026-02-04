"""
Smart Path Extractor - Extração com navegação limitada
"""
import re
from typing import List, Optional
from bs4 import BeautifulSoup
from ..models import ExtractionResult
from ..classify.site_type_enum import SiteType, ExtractionPath
from .fast_path_extractor import FastPathExtractor


class SmartPathExtractor:
    """
    Extração com navegação limitada por budget
    
    Usado para sites CORPORATE_MULTI_PAGE onde dados podem estar em /contato
    """
    
    # Links prioritários para navegação
    NAVIGATION_TARGETS = [
        '/contato', '/contact',
        '/sobre', '/about',
        '/unidades', '/locations',
        '/fale-conosco', '/faleconosco',
        '/onde-estamos'
    ]
    
    MAX_PAGES_TO_VISIT = 3  # Budget rígido
    
    def __init__(self):
        self.fast_path = FastPathExtractor()
    
    def try_extract(self, html: str, site_type: SiteType, 
                    fetcher=None, base_url: str = None) -> ExtractionResult:
        """
        Navega até N páginas buscando dados
        
        Fluxo:
        1. Identificar links candidatos (/contato, /sobre)
        2. Ordenar por relevância
        3. Visitar até MAX_PAGES_TO_VISIT
        4. Para cada página:
           a. Tentar FastPath
           b. Se sucesso → PARAR (early exit)
        5. Agregar resultados
        
        Args:
            html: HTML da página principal
            site_type: Tipo de site
            fetcher: Objeto para fazer requisições HTTP (opcional)
            base_url: URL base para resolver links relativos (opcional)
        
        Returns:
            ExtractionResult: Resultado da extração
        """
        try:
            # Se não tem fetcher, não pode navegar, usa apenas FastPath
            if not fetcher or not base_url:
                return self.fast_path.try_extract(html, site_type)
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Identificar links candidatos
            candidate_links = self._find_candidate_links(soup, base_url)
            
            visited = 0
            best_result = ExtractionResult.failure()
            
            # Tentar FastPath na página atual primeiro
            current_result = self.fast_path.try_extract(html, site_type)
            if current_result.is_valid():
                # EARLY EXIT: Sucesso na página atual
                current_result.extraction_path = ExtractionPath.SMART_PATH
                return current_result
            
            # Navegar páginas candidatas
            for link in candidate_links[:self.MAX_PAGES_TO_VISIT]:
                visited += 1
                
                try:
                    # Fetch via HTTP puro (sem renderização)
                    page_html = fetcher.fetch(link)
                    
                    # Tentar FastPath na sub-página
                    result = self.fast_path.try_extract(page_html, site_type)
                    
                    if result.is_valid():
                        # EARLY EXIT: Sucesso em sub-página
                        result.extraction_path = ExtractionPath.SMART_PATH
                        return result
                    
                    # Guardar melhor resultado até agora
                    if len(result.emails) > len(best_result.emails):
                        best_result = result
                
                except Exception as e:
                    # Falha silenciosa, tentar próximo link
                    continue
            
            # Se encontrou algo (mesmo que parcial), retornar
            if best_result.is_valid():
                best_result.extraction_path = ExtractionPath.SMART_PATH
                return best_result
            
            return ExtractionResult.failure()
        
        except Exception as e:
            return ExtractionResult.failure()
    
    def _find_candidate_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Encontra links candidatos para navegação
        
        Returns:
            Lista de URLs ordenadas por relevância
        """
        candidates = []
        
        # Buscar todos os links
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '').lower().strip()
            
            # Ignorar links vazios, âncoras, javascript, etc
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
            
            # Ignorar links externos (mailto, tel, http externo)
            if href.startswith('mailto:') or href.startswith('tel:'):
                continue
            
            # Resolver URL relativa
            full_url = self._resolve_url(href, base_url)
            if not full_url:
                continue
            
            # Verificar se é link prioritário
            relevance = self._calculate_relevance(href, link.get_text())
            
            if relevance > 0:
                candidates.append((full_url, relevance))
        
        # Ordenar por relevância (maior primeiro)
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Retornar apenas URLs (remover score)
        return [url for url, score in candidates]
    
    def _resolve_url(self, href: str, base_url: str) -> Optional[str]:
        """
        Resolve URL relativa para absoluta
        
        Returns:
            URL completa ou None
        """
        try:
            from urllib.parse import urljoin, urlparse
            
            # Se já é absoluta e do mesmo domínio, OK
            if href.startswith('http'):
                parsed_base = urlparse(base_url)
                parsed_href = urlparse(href)
                
                # Apenas aceitar mesmo domínio
                if parsed_base.netloc == parsed_href.netloc:
                    return href
                else:
                    return None
            
            # Resolver relativa
            full_url = urljoin(base_url, href)
            
            # Validar que ficou no mesmo domínio
            parsed_base = urlparse(base_url)
            parsed_full = urlparse(full_url)
            
            if parsed_base.netloc == parsed_full.netloc:
                return full_url
            
            return None
        
        except:
            return None
    
    def _calculate_relevance(self, href: str, link_text: str) -> int:
        """
        Calcula relevância do link (0-100)
        
        Maior relevância = mais provável ter informações de contato
        
        Returns:
            Score de relevância
        """
        score = 0
        
        href_lower = href.lower()
        text_lower = link_text.lower().strip()
        
        # Verificar palavras-chave no href
        for target in self.NAVIGATION_TARGETS:
            if target in href_lower:
                score += 50  # Alta relevância
                break
        
        # Verificar palavras-chave no texto do link
        contact_keywords = ['contato', 'contact', 'fale', 'onde', 'localização', 'location']
        for keyword in contact_keywords:
            if keyword in text_lower:
                score += 30
                break
        
        # Penalizar links muito longos (provavelmente não são páginas de contato)
        if len(href) > 100:
            score -= 20
        
        # Penalizar links com query strings complexas
        if '?' in href and href.count('=') > 2:
            score -= 10
        
        return max(0, score)
