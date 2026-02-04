"""
Modelos de Dados para Scraping
"""
from dataclasses import dataclass, field
from typing import Optional, List
from .classify.site_type_enum import SiteType, DetectionConfidence, ExtractionPath


@dataclass
class ClassificationResult:
    """Resultado da classificação de site"""
    site_type: SiteType
    confidence: DetectionConfidence
    reasons: List[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)


@dataclass
class ExtractionResult:
    """Resultado da extração de dados"""
    success: bool
    emails: List[str] = field(default_factory=list)
    phones: List[str] = field(default_factory=list)
    address: Optional[str] = None
    company_name: Optional[str] = None
    domain: Optional[str] = None
    url: Optional[str] = None
    html_content: Optional[str] = None
    extraction_path: ExtractionPath = ExtractionPath.FAILED
    time_ms: int = 0

    def is_valid(self) -> bool:
        """Verifica se tem dados mínimos válidos"""
        return bool(self.emails or self.phones)

    @staticmethod
    def success_result(emails: List[str], phones: List[str], address: Optional[str] = None,
                      company_name: Optional[str] = None, domain: Optional[str] = None,
                      url: Optional[str] = None, path: ExtractionPath = ExtractionPath.FAST_PATH) -> 'ExtractionResult':
        """Factory method para resultado de sucesso"""
        return ExtractionResult(
            success=True,
            emails=emails,
            phones=phones,
            address=address,
            company_name=company_name,
            domain=domain,
            url=url,
            extraction_path=path
        )

    @staticmethod
    def failure() -> 'ExtractionResult':
        """Factory method para falha"""
        return ExtractionResult(success=False)

    @staticmethod
    def empty() -> 'ExtractionResult':
        """Factory method para resultado vazio"""
        return ExtractionResult(success=False)


@dataclass
class ScrapingResult:
    """Resultado completo do scraping"""
    success: bool
    data: Optional[ExtractionResult] = None
    classification: Optional[ClassificationResult] = None
    error: Optional[str] = None
    total_time_ms: int = 0
    pages_visited: int = 0
    used_rendering: bool = False

    @staticmethod
    def success_result(data: ExtractionResult, classification: Optional[ClassificationResult] = None) -> 'ScrapingResult':
        """Factory method para sucesso"""
        return ScrapingResult(
            success=True,
            data=data,
            classification=classification
        )

    @staticmethod
    def failure(error: str) -> 'ScrapingResult':
        """Factory method para falha"""
        return ScrapingResult(
            success=False,
            error=error
        )

    @staticmethod
    def abort(reason: str) -> 'ScrapingResult':
        """Factory method para abort"""
        return ScrapingResult(
            success=False,
            error=f"ABORTED: {reason}"
        )


@dataclass
class DOMMetrics:
    """Métricas de análise DOM"""
    repetition_score: float = 0.0  # 0-1
    link_density: float = 0.0      # 0-1
    navigation_complexity: int = 0
    has_pagination: bool = False
    structural_depth: int = 0
    total_tags: int = 0
    total_links: int = 0
