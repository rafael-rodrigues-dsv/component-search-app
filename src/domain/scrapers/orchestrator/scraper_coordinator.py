"""
Scraper Coordinator - Orquestrador principal do fluxo de scraping
"""
import time
from typing import Optional, Dict
from ..models import ScrapingResult, ExtractionResult, ClassificationResult
from ..classify.site_type_enum import SiteType, DetectionConfidence
from ..classify.site_classifier import SiteClassifier
from ..strategy.strategy_factory import StrategyFactory
from ..orchestrator.budget_manager import BudgetManager
from ..fetch.http_fetcher import HttpFetcher
from ..fetch.render_fetcher import RenderFetcher
from ..utils.scraper_logger import ScraperLogger


class ScraperCoordinator:
    """
    Orquestrador principal do scraping inteligente

    Coordena todo o fluxo:
    1. FETCH INICIAL (HTTP puro)
    2. VALIDAÇÃO PRELIMINAR
    3. FAST PATH (tentativa imediata)
    4. CLASSIFICAÇÃO (se Fast Path falhar)
    5. DECISÃO DE RENDERIZAÇÃO
    6. APLICAR ESTRATÉGIA
    7. NORMALIZAÇÃO
    8. RETORNAR RESULTADO
    """

    def __init__(self, logger: Optional[ScraperLogger] = None, headless: bool = True):
        """
        Args:
            logger: Logger opcional
            headless: Modo headless para Playwright (padrão: True)
        """
        self.logger = logger or ScraperLogger('COORDINATOR')
        self.headless = headless  # 🆕 Configurável
        self.http_fetcher = HttpFetcher(self.logger)
        self.render_fetcher = RenderFetcher(self.logger, headless=headless)  # 🆕 Passar headless
        self.classifier = SiteClassifier(self.logger)
        self.strategy_factory = StrategyFactory()

    def scrape(self, url: str, use_rendering: bool = False) -> ScrapingResult:
        """
        Fluxo completo de scraping

        Args:
            url: URL para scraper
            use_rendering: Forçar uso de renderização (opcional)

        Returns:
            ScrapingResult: Resultado completo
        """
        start_time = time.time()

        self.logger.log_step("Iniciando scraping inteligente", 'search')
        self.logger.log('web', f"URL: {url[:70]}")

        # ==========================================
        # 1. FETCH INICIAL (HTTP PURO)
        # ==========================================
        self.logger.log_step("FETCH HTTP", 'web')

        html = self.http_fetcher.fetch(url)

        if not html:
            self.logger.log('error', "Fetch HTTP falhou")
            self.logger.dedent()
            self.logger.dedent()
            return ScrapingResult.abort("HTTP fetch failed")

        self.logger.log('document', f"HTML: {len(html):,} chars")
        self.logger.log_step_end("Fetch concluído", 'success')

        # ==========================================
        # 2. VALIDAÇÕES PRELIMINARES
        # ==========================================
        # Verificar se é PDF
        if url.lower().endswith('.pdf') or 'application/pdf' in html[:1000].lower():
            self.logger.log('warning', "PDF detectado - aplicando PDF_FIRST_STRATEGY")
            self.logger.dedent()
            return self._handle_pdf(url, html, start_time)

        # Verificar tamanho mínimo
        if len(html) < 500:
            self.logger.log('error', f"HTML muito pequeno ({len(html)} chars)")
            self.logger.dedent()
            return ScrapingResult.abort("HTML too small")

        self.logger.log('success', "Validações OK")

        # ==========================================
        # 3. FAST PATH (Tentativa Imediata)
        # ==========================================
        self.logger.log_step("FAST PATH - Tentando extração rápida", 'fire')

        from ..extract.fast_path_extractor import FastPathExtractor
        fast_extractor = FastPathExtractor()

        fast_start = time.time()
        fast_result = fast_extractor.try_extract(html, SiteType.UNKNOWN)
        fast_time_ms = int((time.time() - fast_start) * 1000)

        self.logger.log('clock', f"⚡ {fast_time_ms}ms")

        if fast_result.is_valid():
            self.logger.log('chart', f"Encontrado: {len(fast_result.emails)} email(s), {len(fast_result.phones)} telefone(s)")

            # ✅ CORREÇÃO: Verificar se NÃO é lista E se tem poucos contatos (1-5 = empresa individual)
            is_list = self._looks_like_list(html, fast_result)
            if not is_list:
                self.logger.log('rocket', "EARLY EXIT - Dados válidos no FastPath")

                # Completar metadados
                fast_result.url = url
                fast_result.domain = self._extract_domain(url)
                fast_result.time_ms = fast_time_ms

                total_time_ms = int((time.time() - start_time) * 1000)
                self.logger.log_step_end(f"⚡ TOTAL: {total_time_ms}ms", 'success')
                self.logger.dedent()

                return ScrapingResult.success_result(fast_result)
            else:
                self.logger.log('warning', "Lista detectada - continuando análise completa")
                self.logger.log_step_end()
        else:
            self.logger.log('warning', "Sem dados no FastPath")
            self.logger.log_step_end()

        # ==========================================
        # 4. CLASSIFICAÇÃO
        # ==========================================
        self.logger.log_step("CLASSIFICAÇÃO - Analisando tipo de site", 'magnifier')

        classification = self.classifier.classify(html, url)

        self.logger.log('target', f"Tipo: {classification.site_type.name} | Confiança: {classification.confidence.name}")

        # ✅ CORREÇÃO: Só abortar se for lista E não tiver dados válidos do Fast Path
        if classification.site_type in [SiteType.BUSINESS_DIRECTORY, SiteType.SEARCH_RESULTS]:
            # Se Fast Path encontrou dados válidos (1-5 contatos), continuar
            if fast_result and (fast_result.emails or fast_result.phones) and classification.confidence != DetectionConfidence.HIGH:
                self.logger.log('info', f"⚠️ {classification.site_type.name} mas Fast Path encontrou dados válidos - CONTINUANDO")
            else:
                self.logger.log('warning', f"ABORT - Site é {classification.site_type.name}")
                self.logger.log_step_end()
                self.logger.dedent()
                return ScrapingResult.abort(f"Site type: {classification.site_type.name}")

        self.logger.log_step_end("Classificação concluída", 'success')

        # ==========================================
        # 5. DECISÃO DE RENDERIZAÇÃO
        # ==========================================
        needs_render = use_rendering or self._needs_rendering(html, classification)

        if needs_render:
            # ✅ CORREÇÃO: Deep Search já está usando Playwright (Page renderizado)
            # Não tentar criar novo browser - usar HTML já capturado
            self.logger.log('info', "💡 Renderização detectada necessária, mas já temos HTML do Playwright")
            # HTML já vem do Page do Deep Search scraper, não precisa renderizar novamente
        else:
            self.logger.log('success', "✅ Renderização não necessária (HTML puro suficiente)")

        # ==========================================
        # 6. APLICAR ESTRATÉGIA
        # ==========================================
        self.logger.log_step("ESTRATÉGIA - Aplicando extração", 'target')

        strategy = self.strategy_factory.create(classification.site_type)
        self.logger.log('robot', f"Usando: {strategy.__class__.__name__}")

        # Criar budget para a estratégia
        budget = BudgetManager(classification.site_type)

        # Executar estratégia
        extraction_result = strategy.extract(html, url, self.http_fetcher)

        # Log budget
        self.logger.log('chart', f"Budget: {budget.pages_visited} página(s), {budget.elapsed_ms()}ms")
        self.logger.log_step_end("Estratégia concluída", 'success')

        # ==========================================
        # 7. RESULTADO FINAL
        # ==========================================
        total_time_ms = int((time.time() - start_time) * 1000)

        if extraction_result.is_valid():
            self.logger.log('chart', f"Resultados: {len(extraction_result.emails) if extraction_result.emails else 0} email(s), {len(extraction_result.phones) if extraction_result.phones else 0} telefone(s)")

            self.logger.log('success', f"✅ {extraction_result.company_name or 'N/A'} | {extraction_result.domain or self._extract_domain(url)}")
            self.logger.log('clock', f"⚡ TOTAL: {total_time_ms}ms")

            self.logger.log_step_end("Scraping concluído com sucesso", 'success')

            result = ScrapingResult.success_result(extraction_result, classification)
            result.total_time_ms = total_time_ms
            result.used_rendering = needs_render
            result.pages_visited = budget.pages_visited

            return result
        else:
            self.logger.log('error', "Nenhum dado válido encontrado")
            self.logger.log('clock', f"❌ TOTAL: {total_time_ms}ms")

            self.logger.log_step_end("Scraping falhou", 'error')

            result = ScrapingResult.failure("No valid data found")
            result.classification = classification
            result.total_time_ms = total_time_ms

            return result

    def _needs_rendering(self, html: str, classification: ClassificationResult) -> bool:
        """
        Decide se precisa renderizar com Playwright

        Heurísticas:
        - HTML muito pequeno (< 5KB) = provável SPA
        - Presença de <noscript> com aviso
        - Frameworks JS detectados (React, Vue, Angular)
        - Conteúdo essencial ausente

        Args:
            html: HTML da página
            classification: Classificação do site

        Returns:
            bool: True se precisa renderizar
        """
        # HTML muito pequeno
        if len(html) < 5000:
            self.logger.log('lightbulb', "HTML < 5KB → provável SPA")
            return True

        html_lower = html.lower()

        # Detectar <noscript> com mensagem de JS necessário
        if '<noscript>' in html_lower and 'javascript' in html_lower:
            self.logger.log('lightbulb', "Tag <noscript> presente → JS necessário")
            return True

        # Detectar frameworks JS
        js_frameworks = ['__NEXT_DATA__', 'react', 'vue', 'angular', 'ember']
        if any(fw in html_lower for fw in js_frameworks):
            self.logger.log('lightbulb', "Framework JS detectado → renderizar")
            return True

        return False

    def _looks_like_list(self, html: str, fast_result=None) -> bool:
        """
        Detecta se é lista/diretório (pattern repetitivo)

        ✅ CORREÇÃO: Considerar também número de contatos encontrados

        Args:
            html: HTML da página
            fast_result: Resultado do Fast Path (opcional)

        Returns:
            bool: True se parece lista
        """
        try:
            # ✅ Se Fast Path encontrou poucos contatos (1-5), NÃO é lista
            if fast_result:
                total_contacts = len(fast_result.emails) + len(fast_result.phones)
                if 1 <= total_contacts <= 5:
                    return False  # Empresa individual

                # Se >10 emails de domínios muito diferentes = lista
                if len(fast_result.emails) > 10:
                    unique_domains = set([e.split('@')[1] for e in fast_result.emails if '@' in e])
                    if len(unique_domains) > 5:
                        return True

            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')

            # Contar classes repetidas
            class_counts = {}
            for tag in soup.find_all(class_=True):
                for cls in tag.get('class', []):
                    class_counts[cls] = class_counts.get(cls, 0) + 1

            # ✅ Aumentar threshold: 10 → 15 (menos falsos positivos)
            if any(count >= 15 for count in class_counts.values()):
                return True

            return False
        except:
            return False

    def _handle_pdf(self, url: str, html: str, start_time: float) -> ScrapingResult:
        """
        Trata sites PDF

        Args:
            url: URL do PDF
            html: HTML (pode ser PDF convertido)
            start_time: Tempo de início

        Returns:
            ScrapingResult
        """
        from ..strategy.pdf_first_strategy import PdfFirstStrategy

        strategy = PdfFirstStrategy()
        extraction_result = strategy.extract(html, url)

        total_time_ms = int((time.time() - start_time) * 1000)

        classification = ClassificationResult(
            site_type=SiteType.PDF_FIRST_SITE,
            confidence=DetectionConfidence.MEDIUM,
            reasons=["URL ou Content-Type é PDF"],
            metrics={}
        )

        if extraction_result.is_valid():
            result = ScrapingResult.success_result(extraction_result, classification)
        else:
            result = ScrapingResult.failure("PDF sem dados válidos")
            result.classification = classification

        result.total_time_ms = total_time_ms
        return result

    def _extract_domain(self, url: str) -> str:
        """Extrai domínio da URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return url
