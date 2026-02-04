"""
Classification Rules - Rule Engine para classificação de sites
"""
from typing import List, Tuple
from .site_type_enum import SiteType, DetectionConfidence
from ..models import DOMMetrics, ClassificationResult


class ClassificationRule:
    """Regra individual de classificação"""

    def __init__(self, site_type: SiteType, weight: int, description: str):
        """
        Args:
            site_type: Tipo de site que esta regra detecta
            weight: Peso da regra (0-100)
            description: Descrição da regra
        """
        self.site_type = site_type
        self.weight = weight
        self.description = description

    def evaluate(self, metrics: DOMMetrics, url: str, html: str) -> int:
        """
        Avalia a regra e retorna score (0-100)

        Args:
            metrics: Métricas DOM
            url: URL da página
            html: HTML da página

        Returns:
            int: Score de 0 a 100 (0 = não se aplica, 100 = certeza absoluta)
        """
        raise NotImplementedError("Subclasses devem implementar evaluate()")


class BusinessDirectoryRule(ClassificationRule):
    """Regra para detectar diretórios de empresas"""

    def __init__(self):
        super().__init__(
            site_type=SiteType.BUSINESS_DIRECTORY,
            weight=90,
            description="Detecta diretórios/listas de empresas"
        )

    def evaluate(self, metrics: DOMMetrics, url: str, html: str) -> int:
        score = 0

        # Repetição alta = forte indicador
        if metrics.repetition_score > 0.5:
            score += 40
        elif metrics.repetition_score > 0.3:
            score += 20

        # Densidade de links alta
        if metrics.link_density > 0.3:
            score += 30
        elif metrics.link_density > 0.2:
            score += 15

        # Paginação presente
        if metrics.has_pagination:
            score += 20

        # Palavras-chave na URL
        directory_keywords = ['empresas', 'fornecedores', 'lista', 'diretorio', 'catalogo']
        url_lower = url.lower()
        if any(keyword in url_lower for keyword in directory_keywords):
            score += 10

        return min(score, 100)


class CorporateMultiPageRule(ClassificationRule):
    """Regra para detectar sites corporativos multi-página"""

    def __init__(self):
        super().__init__(
            site_type=SiteType.CORPORATE_MULTI_PAGE,
            weight=80,
            description="Detecta sites corporativos com múltiplas páginas"
        )

    def evaluate(self, metrics: DOMMetrics, url: str, html: str) -> int:
        score = 0

        # Links de navegação presentes
        if metrics.navigation_complexity >= 5:
            score += 50
        elif metrics.navigation_complexity >= 3:
            score += 30
        elif metrics.navigation_complexity >= 1:
            score += 15

        # Repetição baixa (não é lista)
        if metrics.repetition_score < 0.3:
            score += 20

        # Densidade de links moderada
        if 0.1 < metrics.link_density < 0.3:
            score += 15

        # Profundidade estrutural moderada
        if metrics.structural_depth > 5:
            score += 15

        return min(score, 100)


class StaticSinglePageRule(ClassificationRule):
    """Regra para detectar sites estáticos de página única"""

    def __init__(self):
        super().__init__(
            site_type=SiteType.STATIC_SINGLE_PAGE,
            weight=70,
            description="Detecta sites estáticos simples"
        )

    def evaluate(self, metrics: DOMMetrics, url: str, html: str) -> int:
        score = 0

        # Poucos links de navegação
        if metrics.navigation_complexity == 0:
            score += 40
        elif metrics.navigation_complexity <= 2:
            score += 20

        # Repetição baixa
        if metrics.repetition_score < 0.2:
            score += 30

        # Densidade de links baixa
        if metrics.link_density < 0.1:
            score += 20

        # Sem paginação
        if not metrics.has_pagination:
            score += 10

        return min(score, 100)


class FranchiseRule(ClassificationRule):
    """Regra para detectar sites de franquias/múltiplas unidades"""

    def __init__(self):
        super().__init__(
            site_type=SiteType.FRANCHISE,
            weight=85,
            description="Detecta sites de franquias com múltiplas unidades"
        )

    def evaluate(self, metrics: DOMMetrics, url: str, html: str) -> int:
        score = 0

        # Palavras-chave na URL ou HTML
        franchise_keywords = ['unidades', 'franquias', 'filiais', 'lojas', 'locations']
        url_lower = url.lower()
        html_lower = html.lower()[:5000]  # Primeiros 5KB

        if any(keyword in url_lower for keyword in franchise_keywords):
            score += 50

        if any(keyword in html_lower for keyword in franchise_keywords):
            score += 30

        # Repetição moderada (lista de unidades)
        if 0.3 < metrics.repetition_score < 0.6:
            score += 20

        return min(score, 100)


class SearchResultsRule(ClassificationRule):
    """Regra para detectar páginas de resultados de busca"""

    def __init__(self):
        super().__init__(
            site_type=SiteType.SEARCH_RESULTS,
            weight=75,
            description="Detecta páginas de resultados de busca"
        )

    def evaluate(self, metrics: DOMMetrics, url: str, html: str) -> int:
        score = 0

        # Palavras-chave na URL
        search_keywords = ['search', 'busca', 'pesquisa', 'query', 'q=']
        url_lower = url.lower()

        if any(keyword in url_lower for keyword in search_keywords):
            score += 60

        # Paginação presente
        if metrics.has_pagination:
            score += 20

        # Alta densidade de links
        if metrics.link_density > 0.4:
            score += 20

        return min(score, 100)


class PDFFirstSiteRule(ClassificationRule):
    """Regra para detectar sites que são basicamente PDFs"""

    def __init__(self):
        super().__init__(
            site_type=SiteType.PDF_FIRST_SITE,
            weight=100,
            description="Detecta sites que redirecionam para PDF"
        )

    def evaluate(self, metrics: DOMMetrics, url: str, html: str) -> int:
        score = 0

        # URL termina com .pdf
        if url.lower().endswith('.pdf'):
            score = 100

        # Content-Type seria checado antes, mas caso passe...
        if 'application/pdf' in html[:1000].lower():
            score = 100

        return score


class ClassificationRules:
    """
    Rule Engine para classificação de sites

    Aplica múltiplas regras e agrega scores para decidir tipo
    """

    def __init__(self):
        """Inicializa todas as regras"""
        self.rules: List[ClassificationRule] = [
            PDFFirstSiteRule(),          # Maior prioridade
            BusinessDirectoryRule(),
            FranchiseRule(),
            CorporateMultiPageRule(),
            SearchResultsRule(),
            StaticSinglePageRule(),      # Menor prioridade (padrão)
        ]

    def classify(self, metrics: DOMMetrics, url: str, html: str) -> ClassificationResult:
        """
        Aplica todas as regras e retorna classificação

        Args:
            metrics: Métricas DOM
            url: URL da página
            html: HTML da página

        Returns:
            ClassificationResult: Resultado da classificação
        """
        scores = {}
        reasons = []

        # Avaliar cada regra
        for rule in self.rules:
            score = rule.evaluate(metrics, url, html)
            weighted_score = (score * rule.weight) / 100

            if score > 0:
                if rule.site_type not in scores:
                    scores[rule.site_type] = 0

                scores[rule.site_type] += weighted_score

                if score > 30:  # Apenas registrar razões significativas
                    reasons.append(f"{rule.site_type.name}: {rule.description} (score={score})")

        # Se nenhuma regra teve score, é UNKNOWN
        if not scores:
            return ClassificationResult(
                site_type=SiteType.UNKNOWN,
                confidence=DetectionConfidence.LOW,
                reasons=["Nenhuma regra se aplicou"],
                metrics={'raw_scores': {}}
            )

        # Pegar tipo com maior score
        best_type = max(scores.items(), key=lambda x: x[1])
        site_type = best_type[0]
        final_score = best_type[1]

        # Determinar confiança baseado no score
        if final_score > 80:
            confidence = DetectionConfidence.HIGH
        elif final_score > 50:
            confidence = DetectionConfidence.MEDIUM
        else:
            confidence = DetectionConfidence.LOW

        return ClassificationResult(
            site_type=site_type,
            confidence=confidence,
            reasons=reasons,
            metrics={
                'raw_scores': {st.name: s for st, s in scores.items()},
                'final_score': final_score,
                'dom_metrics': {
                    'repetition': metrics.repetition_score,
                    'link_density': metrics.link_density,
                    'navigation': metrics.navigation_complexity,
                    'has_pagination': metrics.has_pagination
                }
            }
        )
