"""
PDF First Strategy - Estratégia para sites que são basicamente PDFs
"""
from ..models import ExtractionResult
from ..classify.site_type_enum import SiteType, ExtractionPath
from ..extract.regex_extractor import RegexExtractor
from .base_strategy import BaseStrategy


class PdfFirstStrategy(BaseStrategy):
    """
    Estratégia para PDF_FIRST_SITE

    Fluxo:
    1. Extrair texto do PDF
    2. Aplicar regex validatório
    3. Normalizar
    """

    def __init__(self):
        super().__init__()
        self.site_type = SiteType.PDF_FIRST_SITE
        self.regex_extractor = RegexExtractor()

    def extract(self, html: str, url: str, fetcher=None) -> ExtractionResult:
        """
        Extração de PDF

        Como não temos biblioteca de PDF instalada ainda,
        tentaremos extrair do HTML (às vezes PDFs são convertidos)
        """
        # Tentar extrair com regex (PDF convertido para HTML pode ter texto)
        result = self.regex_extractor.try_extract(html, self.site_type)

        if result.success:
            result.url = url
            result.domain = self._extract_domain(url)
            result.extraction_path = ExtractionPath.REGEX_PATH

        return result

    def extract_from_pdf_content(self, pdf_bytes: bytes, url: str) -> ExtractionResult:
        """
        Extrai dados diretamente de bytes de PDF

        Requer: PyPDF2 ou pdfplumber

        Args:
            pdf_bytes: Conteúdo do PDF em bytes
            url: URL do PDF

        Returns:
            ExtractionResult
        """
        try:
            # TODO: Implementar quando instalar biblioteca de PDF
            # from PyPDF2 import PdfReader
            # reader = PdfReader(io.BytesIO(pdf_bytes))
            # text = ""
            # for page in reader.pages:
            #     text += page.extract_text()

            # Por enquanto, retornar failure
            result = ExtractionResult.failure()
            result.url = url
            result.domain = self._extract_domain(url)
            return result

        except Exception as e:
            return ExtractionResult.failure()

    def _extract_domain(self, url: str) -> str:
        """Extrai domínio da URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return url
