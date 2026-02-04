"""
Camada de Aplicação - Serviço principal do robô coletor (refatorado)
"""
import random
import time
from typing import List, Dict

from config.settings import (
    BLACKLIST_HOSTS, MAX_EMAILS_PER_SITE,
    RESULTS_PER_TERM_LIMIT, SEARCH_DWELL, COMPLETE_MODE_THRESHOLD
)
from .database_application_service import DatabaseApplicationService
from .user_config_application_service import UserConfigApplicationService
from ...domain.models.collection_result_model import CollectionResultModel
from ...domain.models.collection_stats_model import CollectionStatsModel
from ...domain.models.company_model import CompanyModel
from ...domain.models.search_term_model import SearchTermModel
from ...domain.models.term_result_model import TermResultModel
from ...domain.protocols.scraper_protocol import ScraperProtocol
from ...domain.services.email_domain_service import (
    EmailCollectorInterface, EmailValidationService
)
from ...infrastructure.config.config_manager import ConfigManager
from ...infrastructure.drivers.playwright_manager import PlaywrightManager
from ...infrastructure.logging.structured_logger import StructuredLogger
from ...infrastructure.metrics.performance_tracker import PerformanceTracker
from ...infrastructure.scrapers.duckduckgo_scraper_playwright import DuckDuckGoScraperPlaywright
from ...infrastructure.scrapers.google_scraper_playwright import GoogleScraperPlaywright
from .robot_controller_application_service import is_stop_requested


class EmailApplicationService(EmailCollectorInterface):
    """Serviço de aplicação do PythonSearchApp coletor de e-mails"""

    def __init__(self) -> None:
        # Logger estruturado e métricas
        self.logger = StructuredLogger("email_collector")
        self.config = ConfigManager()
        self.performance_tracker = PerformanceTracker() if self.config.performance_tracking_enabled else None

        # Serviço de banco de dados
        self.db_service = DatabaseApplicationService()

        # Configurações do usuário (inputs do console)
        self.browser: str = UserConfigApplicationService.get_browser()
        self.search_engine: str = UserConfigApplicationService.get_search_engine()
        self.top_results_total: int = UserConfigApplicationService.get_processing_mode()

        # Inicialização de componentes DEPOIS dos inputs
        headless_mode = self.config.get('webdriver.headless', True)
        self.playwright_manager: PlaywrightManager = PlaywrightManager(headless=headless_mode)
        self.scraper: ScraperProtocol = self._setup_scraper()
        self._setup_services()

    def _setup_scraper(self) -> ScraperProtocol:
        """Configura scraper baseado na escolha do usuário"""
        browser_name = "Chromium (Playwright)"

        # Configurar motor de busca
        if self.search_engine == "GOOGLE":
            self.logger.info(f"Usando Google com {browser_name}", engine="Google", browser=browser_name)
            return GoogleScraperPlaywright(None)
        else:
            self.logger.info(f"Usando DuckDuckGo com {browser_name}", engine="DuckDuckGo", browser=browser_name)
            return DuckDuckGoScraperPlaywright(None)

    def _setup_services(self) -> None:
        """Configura serviços de domínio"""
        self.validation_service: EmailValidationService = EmailValidationService()

    def execute(self) -> bool:
        """Executa coleta completa de e-mails"""
        try:
            self.logger.debug("Tentando iniciar Playwright...")
            self.playwright_manager.start()
            page = self.playwright_manager.get_page()

            if not page:
                self.logger.error("Falha ao iniciar Playwright")
                return False
            self.logger.debug("Playwright iniciado com sucesso")

            # Configurar scraper com a página
            self.scraper.page = page

            # Obter termos do banco
            # Garantir que os termos estejam inicializados no banco
            try:
                initialized = self.db_service.initialize_search_terms()
                self.logger.info(f"Termos inicializados: {initialized}")
            except Exception:
                self.logger.warning("Falha ao inicializar termos dinamicamente; prosseguindo com termos existentes no banco")

            terms_data = self.db_service.get_search_terms()
            if not terms_data:
                self.logger.error("Nenhum termo de busca encontrado - abortando execução")
                # Emit extra debug: try to query count directly from domain service
                try:
                    cnt = self.db_service.domain_service.count_total_search_terms()
                    self.logger.debug(f"DomainService reports total_terms={cnt}")
                except Exception as ex:
                    self.logger.debug(f"Erro ao obter count_total_search_terms: {ex}")
                return False

            # Log summary of terms retrieved (first 3) for debugging
            try:
                sample = terms_data[:3]
                self.logger.debug(f"Obtidos {len(terms_data)} termos para processamento. Amostra: {sample}")
            except Exception:
                pass

            # Converter para SearchTermModel
            terms = [SearchTermModel(query=t['termo'], location='São Paulo', category='elevadores', pages=3) for t in
                     terms_data]
            result = self.collect_emails(terms, terms_data)
            return result.success

        finally:
            self.playwright_manager.stop()

    def collect_emails(self, terms: List[SearchTermModel], terms_data: List[Dict]) -> CollectionResultModel:
        """Coleta e-mails usando termos de busca"""
        start_time = time.time()
        stats = self._initialize_collection_stats(terms)

        self.logger.info("Iniciando coleta",
                         terms_count=len(terms),
                         mode="completo")

        for i, (term, term_data) in enumerate(zip(terms, terms_data), 1):
            # Checar pedido de parada cooperativa
            if is_stop_requested():
                self.logger.info("Parada solicitada - encerrando coleta")
                break

            # Antes de iniciar um termo, checar novamente
            if is_stop_requested():
                self.logger.info("Parada solicitada antes de processar termo")
                break
            if not self._execute_search_for_term(term, i, len(terms)):
                self.db_service.update_term_status(term_data['id'], 'ERRO')
                continue

            term_result = self._process_single_term(term, term_data, stats, i, len(terms))
            stats.update(term_result)

            # Atualizar status do termo no banco
            self.db_service.update_term_status(term_data['id'], 'CONCLUIDO')

        return self._finalize_collection(stats, start_time)

    def _initialize_collection_stats(self, terms: List[SearchTermModel]) -> CollectionStatsModel:
        """Inicializa estatísticas da coleta"""
        total_expected = len(terms) * RESULTS_PER_TERM_LIMIT
        return CollectionStatsModel(start_time=time.time())

    def _execute_search_for_term(self, term: SearchTermModel, current: int, total: int) -> bool:
        """Executa busca para um termo específico"""
        self.logger.info("Processando termo",
                         term=self.logger._sanitize_input(term.query),
                         progress=f"{current}/{total}",
                         mode="completo")

        # Verificar se driver ainda está ativo
        if not self._check_driver_health():
            self.logger.warning("Driver inativo - reiniciando")
            if not self._restart_driver():
                self.logger.error("Falha ao reiniciar driver")
                return False

        if self.performance_tracker:
            with self.performance_tracker.track_operation(f"search_term_{term.query}"):
                search_result = self.scraper.search(term.query)
        else:
            search_result = self.scraper.search(term.query)

        if not search_result:
            self.logger.error("Busca falhou", term=self.logger._sanitize_input(term.query))
            return False
        return True

    def _process_single_term(self, term: SearchTermModel, term_data: Dict, stats: CollectionStatsModel, current: int,
                             total: int) -> TermResultModel:
        """Processa um único termo e retorna resultado"""
        term_saved = self._process_term_results(term, term_data,
                                                stats.total_expected if hasattr(stats, 'total_expected') else 1000,
                                                stats.total_processed)

        self.logger.info("Termo concluído",
                         term=self.logger._sanitize_input(term.query),
                         saved_count=term_saved,
                         progress=f"{current}/{total}")

        return TermResultModel(
            saved_count=term_saved,
            processed_count=term_saved,  # Simplificado por agora
            success=True,
            term_query=term.query
        )

    def _finalize_collection(self, stats: CollectionStatsModel, start_time: float) -> CollectionResultModel:
        """Finaliza coleta e retorna resultado"""
        duration = time.time() - start_time

        self.logger.info("Coleta finalizada",
                         total_saved=stats.total_saved,
                         terms_completed=stats.terms_completed,
                         duration_seconds=round(duration, 2))

        # Log de métricas de performance se habilitado
        if self.performance_tracker:
            perf_stats = self.performance_tracker.get_stats()
            self.logger.info("Métricas de performance",
                             avg_duration=round(perf_stats.get('avg_duration', 0), 2),
                             success_rate=round(perf_stats.get('success_rate', 0) * 100, 1),
                             total_operations=perf_stats.get('total_operations', 0))

        return CollectionResultModel(
            success=True,
            stats=stats,
            duration_seconds=duration,
            message=f"Coleta concluída com {stats.total_saved} empresas salvas"
        )

    def _process_term_results(self, term: SearchTermModel, term_data: Dict, total_expected: int,
                              global_processed: int) -> int:
        """Processa resultados de um termo específico"""
        term_saved = 0
        results_processed = 0

        for page in range(term.pages):
            # Checar parada antes de processar cada página
            if is_stop_requested():
                self.logger.info("Parada solicitada - interrompendo paginação")
                break
            links = self.scraper.get_result_links(BLACKLIST_HOSTS)
            if not links:
                break

            for link in links:
                # Checar parada em cada iteração de link (ponto de cooperação)
                if is_stop_requested():
                    self.logger.info("Parada solicitada - interrompendo processamento de links")
                    break

                results_processed += 1
                global_processed += 1
                domain = self.validation_service.extract_domain_from_url(link)

                # Verificar se domínio já foi visitado (banco)
                if self.db_service.is_domain_visited(domain):
                    self.logger.debug("Site já visitado", domain=self.logger._sanitize_input(domain))
                    continue

                self.logger.info("Acessando site",
                                 domain=self.logger._sanitize_input(domain),
                                 progress=f"{global_processed}/{total_expected}")

                if self.performance_tracker:
                    with self.performance_tracker.track_operation(f"extract_data_{domain}"):
                        company = self.scraper.extract_company_data(link, MAX_EMAILS_PER_SITE)
                else:
                    company = self.scraper.extract_company_data(link, MAX_EMAILS_PER_SITE)

                company.search_term = term.query

                if self._save_company_to_database(company, domain, term_data['id']):
                    term_saved += 1

                # Dormir entre acessos, mas de forma interrompível
                sleep_time = random.uniform(*SEARCH_DWELL)
                # Dividir sleep em pequenos pedaços para checar parada
                waited = 0.0
                step = 0.25
                while waited < sleep_time:
                    if is_stop_requested():
                        self.logger.info('Parada solicitada durante sleep; abortando sleep')
                        break
                    time.sleep(min(step, sleep_time - waited))
                    waited += step

            # Próxima página
            if page < term.pages - 1:
                if hasattr(self.scraper, 'go_to_next_page'):
                    if not self.scraper.go_to_next_page():
                        self.logger.info("Não há mais páginas", term=self.logger._sanitize_input(term.query))
                        break

        return term_saved

    def _save_company_to_database(self, company: CompanyModel, domain: str, termo_id: int) -> bool:
        """Salva empresa no banco Access (sempre salva, mesmo sem dados)"""
        # Processar e-mails
        new_emails = []
        if company.emails and company.emails.strip():
            email_list = [e.strip() for e in company.emails.split(';') if e.strip()]
            new_emails = [e for e in email_list if not self.db_service.is_email_collected(e)]

        # Processar telefones
        telefones_data = []
        if company.phone and company.phone.strip():
            phone_list = [p.strip() for p in company.phone.split(';') if p.strip()]
            for phone in phone_list:
                telefones_data.append({
                    'original': phone,
                    'formatted': phone,  # Simplificado por agora
                    'ddd': phone[:2] if len(phone) >= 10 else '',
                    'tipo': 'CELULAR' if len(phone) == 11 else 'FIXO'
                })

        # Salvar no banco (sempre salva, mesmo sem e-mails/telefones)
        success = self.db_service.save_company_data(
            termo_id=termo_id,
            site_url=company.url,
            domain=domain,
            motor_busca=self.search_engine,
            emails=new_emails,
            telefones=telefones_data,
            nome_empresa=getattr(company, 'name', None),
            html_content=getattr(company, 'html_content', None),
            termo_busca=company.search_term
        )

        if success:
            # TB_EMPRESAS sempre é salva
            tables_saved = ["TB_EMPRESAS"]
            
            # Outras tabelas só se houver dados válidos
            if new_emails:
                tables_saved.append("TB_EMAILS")
            if telefones_data:
                tables_saved.append("TB_TELEFONES")
            if company.html_content:
                # Verificar se endereço foi extraído
                try:
                    from src.infrastructure.utils.address_extractor import AddressExtractor
                    address_model = AddressExtractor.extract_from_html(company.html_content)
                    if address_model and address_model.is_valid():
                        tables_saved.extend(["TB_ENDERECOS", "TB_CEP_ENRICHMENT", "TB_GEOLOCALIZACAO"])
                except Exception:
                    pass
            
            # TB_PLANILHA só se houver dados coletados
            if new_emails or telefones_data:
                tables_saved.append("TB_PLANILHA")
                status_msg = "com dados coletados"
            else:
                status_msg = "sem dados (NAO_COLETADO)"
            
            self.logger.info(f"Empresa salva no banco {status_msg}",
                             domain=self.logger._sanitize_input(domain),
                             emails_count=len(new_emails),
                             phones_count=len(telefones_data),
                             tables=" | ".join(tables_saved))

        return success

    def _check_driver_health(self) -> bool:
        """Verifica se o Playwright ainda está ativo"""
        try:
            page = self.playwright_manager.get_page()
            if not page:
                return False
            page.url
            return True
        except Exception:
            return False

    def _restart_driver(self) -> bool:
        """Reinicia o Playwright"""
        try:
            self.playwright_manager.stop()
            self.playwright_manager.start()
            page = self.playwright_manager.get_page()
            if page:
                self.scraper.page = page
                return True
            return False
        except Exception:
            return False

    def add_emails(self, empresa_id: int, emails: list, domain_email: str):
        """Compat wrapper — adiciona e-mails usando o repositório de e-mails."""
        try:
            from src.infrastructure.repositories.emails_repository import EmailsRepository
            repo = EmailsRepository()
            return repo.insert_emails(empresa_id, emails, domain_email)
        except Exception:
            # Fallback: delegar ao DatabaseApplicationService se implementado
            try:
                return self.db_service.domain_service.save_emails(empresa_id, emails, domain_email)
            except Exception:
                return None

    def is_collected(self, email: str) -> bool:
        """Compat wrapper — verifica se o e-mail já foi coletado."""
        try:
            # Preferir delegar para o DatabaseApplicationService que encapsula regras
            return self.db_service.is_email_collected(email)
        except Exception:
            # fallback to repository
            try:
                from src.infrastructure.repositories.emails_repository import EmailsRepository
                repo = EmailsRepository()
                return repo.is_email_collected(email)
            except Exception:
                return False

    def get_paginated_emails(self, empresa_id: int = None, limit: int = 10, offset: int = 0):
        try:
            from src.infrastructure.repositories.emails_repository import EmailsRepository
            repo = EmailsRepository()
            total = repo.count(empresa_id)
            models = repo.fetch_models_paginated(empresa_id=empresa_id, limit=limit, offset=offset)
            items = [m.to_api_dict() for m in models]
            try:
                limit = int(limit) if limit else 10
                offset = int(offset) if offset else 0
            except Exception:
                limit = 10
                offset = 0
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            current_page = (offset // limit) + 1 if limit > 0 else 1
            return {'emails': items, 'pagination': {'total': total, 'limit': limit, 'offset': offset, 'total_pages': total_pages, 'current_page': current_page, 'has_next': current_page < total_pages, 'has_previous': current_page > 1}}
        except Exception:
            return {'emails': [], 'pagination': {'total': 0, 'limit': limit, 'offset': offset, 'total_pages': 1, 'current_page': 1, 'has_next': False, 'has_previous': False}}

    def collect_single_term_with_callbacks(
        self,
        term: str,
        progress_callback=None,
        should_stop_callback=None,
        db_lock=None,
        browser: str = None,
        engine: str = None,
        headless: bool = None
    ) -> Dict:
        """
        Coleta dados para um único termo com suporte a callbacks e thread-safety

        Args:
            term: Termo de busca
            progress_callback: Função callback(progress: int, action: str)
            should_stop_callback: Função callback() -> bool para verificar se deve parar
            db_lock: Lock threading para operações no banco (thread-safe)
            browser: Browser a usar (CHROME ou BRAVE), se None usa self.browser
            engine: Engine de busca (GOOGLE ou DUCKDUCKGO), se None usa self.search_engine
            headless: Se True executa em modo headless, se None usa config padrão

        Returns:
            Dict com resultado: {'success': bool, 'companies_found': int, 'error': str}
        """
        try:
            # Usar parâmetros fornecidos ou fallback para self
            actual_browser = browser if browser is not None else self.browser
            actual_engine = engine if engine is not None else self.search_engine

            print(f"[PLAYWRIGHT] 🎭 Inicializando Playwright (browser={actual_browser}, headless={headless})...")

            # Criar instância própria do Playwright (isolado por thread)
            playwright_manager = PlaywrightManager(
                headless=headless if headless is not None else True,
                browser_type=actual_browser  # CHROME, BRAVE, etc.
            )
            playwright_manager.start()
            page = playwright_manager.get_page()

            if not page:
                print(f"[PLAYWRIGHT] ❌ Falha ao obter página!")
                return {'success': False, 'error': 'Falha ao iniciar Playwright'}

            print(f"[PLAYWRIGHT] ✅ Playwright iniciado com sucesso!")

            # Criar scraper isolado baseado no engine escolhido
            if actual_engine == "GOOGLE":
                scraper = GoogleScraperPlaywright(page)
                print(f"[PLAYWRIGHT] ✅ Google Scraper Playwright criado")
            else:
                scraper = DuckDuckGoScraperPlaywright(page)
                print(f"[PLAYWRIGHT] ✅ DuckDuckGo Scraper Playwright criado")

            try:
                # Notificar início
                if progress_callback:
                    progress_callback(5, f"Buscando: {term}")

                # Executar busca
                search_result = scraper.search(term)
                if not search_result:
                    return {'success': False, 'error': 'Busca falhou'}

                if progress_callback:
                    progress_callback(15, "Busca concluída, coletando resultados...")

                # Obter termo do banco (thread-safe com lock)
                if db_lock:
                    with db_lock:
                        terms_data = [t for t in self.db_service.get_search_terms() if t['termo'] == term]
                else:
                    terms_data = [t for t in self.db_service.get_search_terms() if t['termo'] == term]

                if not terms_data:
                    return {'success': False, 'error': 'Termo não encontrado no banco'}

                term_data = terms_data[0]
                termo_id = term_data['id']

                # Processar resultados
                companies_found = 0
                total_links = 0

                # Processar páginas
                for page in range(3):  # 3 páginas por termo
                    # Verificar se deve parar
                    if should_stop_callback and should_stop_callback():
                        if progress_callback:
                            progress_callback(100, "Parado pelo usuário")
                        break

                    links = scraper.get_result_links(BLACKLIST_HOSTS)
                    if not links:
                        break

                    total_links += len(links)

                    for i, link in enumerate(links):
                        # Verificar se deve parar
                        if should_stop_callback and should_stop_callback():
                            break

                        # Atualizar progresso
                        progress_pct = 15 + int((i + 1) / len(links) * 70)
                        if progress_callback:
                            progress_callback(progress_pct, f"Processando site {i+1}/{len(links)}")

                        domain = self.validation_service.extract_domain_from_url(link)

                        # Verificar domínio (thread-safe com lock)
                        is_visited = False
                        if db_lock:
                            with db_lock:
                                is_visited = self.db_service.is_domain_visited(domain)
                        else:
                            is_visited = self.db_service.is_domain_visited(domain)

                        if is_visited:
                            continue

                        # Extrair dados
                        company = scraper.extract_company_data(link, MAX_EMAILS_PER_SITE)
                        company.search_term = term

                        # Salvar no banco (thread-safe com lock)
                        saved = False
                        if db_lock:
                            with db_lock:
                                saved = self._save_company_to_database(company, domain, termo_id)
                        else:
                            saved = self._save_company_to_database(company, domain, termo_id)

                        if saved:
                            companies_found += 1

                        # Pequeno delay
                        time.sleep(random.uniform(0.1, 0.3))

                    # Próxima página
                    if page < 2:
                        if hasattr(scraper, 'go_to_next_page'):
                            if not scraper.go_to_next_page():
                                break

                # Atualizar status do termo (thread-safe com lock)
                if db_lock:
                    with db_lock:
                        self.db_service.update_term_status(termo_id, 'CONCLUIDO')
                else:
                    self.db_service.update_term_status(termo_id, 'CONCLUIDO')

                # Notificar conclusão
                if progress_callback:
                    progress_callback(100, f"Concluído: {companies_found} empresas")

                return {
                    'success': True,
                    'companies_found': companies_found,
                    'links_processed': total_links
                }

            finally:
                playwright_manager.stop()

        except Exception as e:
            self.logger.error(f"Erro ao processar termo '{term}': {e}")
            return {'success': False, 'error': str(e)}
