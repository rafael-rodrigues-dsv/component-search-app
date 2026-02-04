"""
Site Classifier - Classificador principal de tipos de site
"""
from typing import Dict, Optional
from ..models import ClassificationResult, DOMMetrics
from ..utils.scraper_logger import ScraperLogger
from .dom_analyzer import DOMAnalyzer
from .classification_rules import ClassificationRules
from .site_type_enum import SiteType, DetectionConfidence


class SiteClassifier:
    """
    Classificador principal de sites

    Combina análise DOM com regras de negócio para classificar tipo de site
    """

    def __init__(self, logger: Optional[ScraperLogger] = None):
        """
        Args:
            logger: Logger opcional
        """
        self.logger = logger or ScraperLogger('CLASSIFIER')
        self.dom_analyzer = DOMAnalyzer()
        self.rules = ClassificationRules()

    def classify(self, html: str, url: str,
                response_headers: Optional[Dict] = None) -> ClassificationResult:
        """
        Classifica site aplicando regras em ordem de prioridade

        Fluxo:
        1. Verificar Content-Type (PDF?)
        2. Analisar estrutura DOM (repetição, links)
        3. Analisar URL (padrões conhecidos)
        4. Aplicar regras de negócio
        5. Retornar tipo + confiança

        Args:
            html: HTML da página
            url: URL da página
            response_headers: Headers HTTP (opcional)

        Returns:
            ClassificationResult: Resultado da classificação
        """
        self.logger.log('target', "Iniciando classificação")

        # ==========================================
        # 1. VERIFICAR CONTENT-TYPE
        # ==========================================
        if response_headers:
            content_type = response_headers.get('Content-Type', '').lower()
            if 'application/pdf' in content_type:
                self.logger.log('success', "Content-Type: PDF detectado")
                return ClassificationResult(
                    site_type=SiteType.PDF_FIRST_SITE,
                    confidence=DetectionConfidence.HIGH,
                    reasons=["Content-Type é application/pdf"],
                    metrics={'content_type': content_type}
                )

        # ==========================================
        # 2. ANALISAR ESTRUTURA DOM
        # ==========================================
        self.logger.log('magnifier', "Analisando estrutura DOM...")
        metrics = self.dom_analyzer.analyze(html)

        self.logger.log('chart', f"Repetição: {metrics.repetition_score:.2f} | " +
                                 f"Links: {metrics.link_density:.2f} | " +
                                 f"Nav: {metrics.navigation_complexity}")

        # ==========================================
        # 3. APLICAR REGRAS DE CLASSIFICAÇÃO
        # ==========================================
        self.logger.log('robot', "Aplicando regras de classificação...")
        classification = self.rules.classify(metrics, url, html)

        # ==========================================
        # 4. LOG RESULTADO
        # ==========================================
        self.logger.log_classification(
            classification.site_type.name,
            classification.confidence.name
        )

        if self.logger.scraper_name != 'CLASSIFIER':
            # Log razões (apenas se verbose)
            for i, reason in enumerate(classification.reasons[:3], 1):
                self.logger.log('lightbulb', f"Razão {i}: {reason[:60]}")

        return classification

    def classify_fast(self, html: str, url: str) -> SiteType:
        """
        Classificação rápida sem análise profunda

        Usado quando precisamos apenas do tipo, sem métricas

        Args:
            html: HTML da página
            url: URL da página

        Returns:
            SiteType: Tipo de site classificado
        """
        # Verificações rápidas por URL
        url_lower = url.lower()

        # PDF
        if url_lower.endswith('.pdf'):
            return SiteType.PDF_FIRST_SITE

        # Search results
        if any(keyword in url_lower for keyword in ['search', 'busca', 'q=', 'query']):
            return SiteType.SEARCH_RESULTS

        # Business directory
        if any(keyword in url_lower for keyword in ['empresas', 'fornecedores', 'lista']):
            return SiteType.BUSINESS_DIRECTORY

        # Análise rápida de HTML
        html_lower = html.lower()[:10000]  # Primeiros 10KB

        # Franchise
        if any(keyword in html_lower for keyword in ['unidades', 'franquias', 'filiais']):
            return SiteType.FRANCHISE

        # Corporate (tem links de contato/sobre)
        if any(keyword in html_lower for keyword in ['contato', 'sobre', 'contact', 'about']):
            return SiteType.CORPORATE_MULTI_PAGE

        # Default: Static
        return SiteType.STATIC_SINGLE_PAGE

    def get_classification_summary(self, classification: ClassificationResult) -> str:
        """
        Gera resumo textual da classificação

        Args:
            classification: Resultado da classificação

        Returns:
            str: Resumo formatado
        """
        lines = []
        lines.append(f"Tipo: {classification.site_type.name}")
        lines.append(f"Confiança: {classification.confidence.name}")

        if classification.metrics:
            dom = classification.metrics.get('dom_metrics', {})
            if dom:
                lines.append(f"Repetição DOM: {dom.get('repetition', 0):.2f}")
                lines.append(f"Densidade Links: {dom.get('link_density', 0):.2f}")
                lines.append(f"Nav Complexity: {dom.get('navigation', 0)}")

        return " | ".join(lines)
