"""
Extraction Chain - Chain of Responsibility para extração de dados
"""
import time
from typing import Optional
from ..models import ExtractionResult
from ..classify.site_type_enum import SiteType
from ..utils.scraper_logger import ScraperLogger
from .fast_path_extractor import FastPathExtractor
from .smart_path_extractor import SmartPathExtractor
from .regex_extractor import RegexExtractor


class ExtractionChain:
    """
    Chain of Responsibility para extração de dados

    Tentativas ordenadas (do mais rápido ao mais lento):
    1. FastPath (CSS selectors) - < 100ms
    2. SmartPath (navegação limitada) - < 1s
    3. Regex (fallback) - < 200ms

    Para assim que um extractor tiver sucesso (Early Exit)
    """

    def __init__(self, logger: Optional[ScraperLogger] = None):
        """
        Args:
            logger: Logger opcional para transparência
        """
        self.logger = logger or ScraperLogger('EXTRACTION')

        # Inicializar extractors
        self.fast_path = FastPathExtractor()
        self.smart_path = SmartPathExtractor()
        self.regex = RegexExtractor()

    def extract(self, html: str, site_type: SiteType,
                fetcher=None, base_url: str = None) -> ExtractionResult:
        """
        Executa chain até ter sucesso ou esgotar tentativas

        Args:
            html: HTML da página
            site_type: Tipo de site classificado
            fetcher: Objeto para requisições HTTP (opcional, para SmartPath)
            base_url: URL base (opcional, para SmartPath)

        Returns:
            ExtractionResult: Melhor resultado encontrado
        """
        self.logger.log('magnifier', "Iniciando chain de extração")

        # ==========================================
        # TENTATIVA 1: FAST PATH (< 100ms)
        # ==========================================
        self.logger.log('rocket', "Tentativa 1: FastPath (CSS selectors)")
        start = time.time()

        result = self.fast_path.try_extract(html, site_type)
        elapsed_ms = int((time.time() - start) * 1000)

        self.logger.log_performance("FastPath", elapsed_ms)

        if result.is_valid():
            self.logger.log('success', f"FastPath SUCCESS: {len(result.emails)} emails, {len(result.phones)} phones")
            result.time_ms = elapsed_ms
            return result
        else:
            self.logger.log('warning', "FastPath falhou, tentando SmartPath...")

        # ==========================================
        # TENTATIVA 2: SMART PATH (< 1s)
        # ==========================================
        # Apenas se tiver fetcher e for tipo multi-página
        if fetcher and base_url and self._should_try_smart_path(site_type):
            self.logger.log('robot', "Tentativa 2: SmartPath (navegação limitada)")
            start = time.time()

            result = self.smart_path.try_extract(html, site_type, fetcher, base_url)
            elapsed_ms = int((time.time() - start) * 1000)

            self.logger.log_performance("SmartPath", elapsed_ms)

            if result.is_valid():
                self.logger.log('success', f"SmartPath SUCCESS: {len(result.emails)} emails, {len(result.phones)} phones")
                result.time_ms = elapsed_ms
                return result
            else:
                self.logger.log('warning', "SmartPath falhou, tentando Regex...")
        else:
            self.logger.log('lightbulb', "SmartPath pulado (tipo de site não suporta ou sem fetcher)")

        # ==========================================
        # TENTATIVA 3: REGEX (fallback)
        # ==========================================
        self.logger.log('fire', "Tentativa 3: Regex (fallback)")
        start = time.time()

        result = self.regex.try_extract(html, site_type)
        elapsed_ms = int((time.time() - start) * 1000)

        self.logger.log_performance("Regex", elapsed_ms)

        if result.is_valid():
            self.logger.log('success', f"Regex SUCCESS: {len(result.emails)} emails, {len(result.phones)} phones")
            result.time_ms = elapsed_ms
            return result
        else:
            self.logger.log('error', "Todas tentativas falharam")

        # ==========================================
        # NENHUM TEVE SUCESSO
        # ==========================================
        return ExtractionResult.failure()

    def _should_try_smart_path(self, site_type: SiteType) -> bool:
        """
        Verifica se vale a pena tentar SmartPath para este tipo de site

        Returns:
            bool: True se deve tentar
        """
        # Tipos que se beneficiam de navegação
        smart_path_types = {
            SiteType.CORPORATE_MULTI_PAGE,
            SiteType.FRANCHISE,
            SiteType.UNKNOWN  # Tentar por garantia
        }

        return site_type in smart_path_types

    def extract_with_timeout(self, html: str, site_type: SiteType,
                            timeout_seconds: float = 5.0,
                            fetcher=None, base_url: str = None) -> ExtractionResult:
        """
        Executa extração com timeout

        Args:
            html: HTML da página
            site_type: Tipo de site
            timeout_seconds: Timeout em segundos
            fetcher: Objeto para requisições (opcional)
            base_url: URL base (opcional)

        Returns:
            ExtractionResult: Resultado ou timeout
        """
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError("Extraction timeout")

        try:
            # Configurar timeout (apenas Unix/Linux)
            if hasattr(signal, 'SIGALRM'):
                signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(timeout_seconds))

            result = self.extract(html, site_type, fetcher, base_url)

            if hasattr(signal, 'SIGALRM'):
                signal.alarm(0)  # Cancelar timeout

            return result

        except TimeoutError:
            self.logger.log('error', f"Extraction timeout ({timeout_seconds}s)")
            return ExtractionResult.failure()

        except Exception as e:
            self.logger.log('error', f"Extraction error: {str(e)[:50]}")
            return ExtractionResult.failure()
