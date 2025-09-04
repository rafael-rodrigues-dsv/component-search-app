"""
Camada de Aplicação - Serviço principal do robô coletor (refatorado)
"""
import random
import time
from typing import List, Dict, Set, Optional, Union

from config.settings import (
    BLACKLIST_HOSTS, MAX_EMAILS_PER_SITE,
    RESULTS_PER_TERM_LIMIT, SEARCH_DWELL, COMPLETE_MODE_THRESHOLD
)
from .user_config_service import UserConfigService
from .database_service import DatabaseService
from ...domain.services.email_domain_service import (
    EmailCollectorInterface, EmailValidationService
)
from ...domain.factories.search_term_factory import SearchTermFactory
from ...domain.models.search_term_model import SearchTermModel
from ...domain.models.company_model import CompanyModel
from ...domain.models.term_result_model import TermResultModel
from ...domain.models.collection_stats_model import CollectionStatsModel
from ...domain.models.collection_result_model import CollectionResultModel
from ...domain.protocols.scraper_protocol import ScraperProtocol
from ...infrastructure.logging.structured_logger import StructuredLogger
from ...infrastructure.repositories.data_repository import JsonRepository, ExcelRepository
from ...infrastructure.scrapers.duckduckgo_scraper import DuckDuckGoScraper
from ...infrastructure.scrapers.google_scraper import GoogleScraper
from ...infrastructure.storage.data_storage import DataStorage
from ...infrastructure.drivers.web_driver import WebDriverManager
from ...infrastructure.metrics.performance_tracker import PerformanceTracker
from ...infrastructure.config.config_manager import ConfigManager


class EmailApplicationService(EmailCollectorInterface):
    """Serviço de aplicação do PythonSearchApp coletor de e-mails"""

    def __init__(self) -> None:
        # Logger estruturado e métricas
        self.logger = StructuredLogger("email_collector")
        self.config = ConfigManager()
        self.performance_tracker = PerformanceTracker() if self.config.performance_tracking_enabled else None

        # Configurações do usuário
        self.browser: str = UserConfigService.get_browser()
        self.search_engine: str = UserConfigService.get_search_engine()

        # Serviço de banco de dados
        self.db_service = DatabaseService()

        # Inicialização de componentes
        self.driver_manager: WebDriverManager = WebDriverManager()
        self.scraper: ScraperProtocol = self._setup_scraper()
        self._setup_services()

        # Configuração final
        self.top_results_total: int = UserConfigService.get_processing_mode()

    def _setup_scraper(self) -> ScraperProtocol:
        """Configura scraper baseado na escolha do usuário"""
        # Configurar navegador
        if self.browser == "BRAVE":
            self.driver_manager.browser = "brave"
            browser_name = "Brave"
        else:
            self.driver_manager.browser = "chrome"
            browser_name = "Chrome"

        # Configurar motor de busca
        if self.search_engine == "GOOGLE":
            self.logger.info(f"Usando Google com {browser_name}", engine="Google", browser=browser_name)
            return GoogleScraper(None)
        else:
            self.logger.info(f"Usando DuckDuckGo com {browser_name}", engine="DuckDuckGo", browser=browser_name)
            return DuckDuckGoScraper(self.driver_manager)

    def _setup_services(self) -> None:
        """Configura serviços de domínio"""
        self.validation_service: EmailValidationService = EmailValidationService()

    def execute(self) -> bool:
        """Executa coleta completa de e-mails"""
        try:
            if not self.driver_manager.start_driver():
                self.logger.error("Falha ao iniciar driver")
                return False

            if self.search_engine == "GOOGLE":
                self.scraper.driver = self.driver_manager.driver

            # Obter termos do banco
            terms_data = self.db_service.get_search_terms()
            if not terms_data:
                self.logger.error("Nenhum termo de busca encontrado")
                return False

            # Converter para SearchTermModel
            terms = [SearchTermModel(query=t['termo'], location='São Paulo', category='elevadores', pages=3) for t in
                     terms_data]
            result = self.collect_emails(terms, terms_data)
            return result.success

        finally:
            self.driver_manager.close_driver()

    def collect_emails(self, terms: List[SearchTermModel], terms_data: List[Dict]) -> CollectionResultModel:
        """Coleta e-mails usando termos de busca"""
        start_time = time.time()
        stats = self._initialize_collection_stats(terms)

        self.logger.info("Iniciando coleta",
                         terms_count=len(terms),
                         mode="completo" if self.top_results_total > COMPLETE_MODE_THRESHOLD else "lote")

        for i, (term, term_data) in enumerate(zip(terms, terms_data), 1):
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
        if self.top_results_total > COMPLETE_MODE_THRESHOLD:
            total_expected = len(terms) * RESULTS_PER_TERM_LIMIT
        else:
            total_expected = len(terms) * self.top_results_total

        return CollectionStatsModel(start_time=time.time())

    def _execute_search_for_term(self, term: SearchTermModel, current: int, total: int) -> bool:
        """Executa busca para um termo específico"""
        mode_text = "completo" if self.top_results_total > COMPLETE_MODE_THRESHOLD else f"lote ({self.top_results_total})"
        self.logger.info("Processando termo",
                         term=self.logger._sanitize_input(term.query),
                         progress=f"{current}/{total}",
                         mode=mode_text)

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
            if results_processed >= self.top_results_total:
                break

            links = self.scraper.get_result_links(BLACKLIST_HOSTS)
            if not links:
                break

            for link in links:
                if results_processed >= self.top_results_total:
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

                time.sleep(random.uniform(*SEARCH_DWELL))

            # Próxima página
            if page < term.pages - 1 and results_processed < self.top_results_total:
                if hasattr(self.scraper, 'go_to_next_page'):
                    if not self.scraper.go_to_next_page():
                        self.logger.info("Não há mais páginas", term=self.logger._sanitize_input(term.query))
                        break

        return term_saved

    def _save_company_to_database(self, company: CompanyModel, domain: str, termo_id: int) -> bool:
        """Salva empresa no banco Access"""
        if not company.emails or not company.emails.strip():
            self.logger.debug("Sem e-mail válido", domain=self.logger._sanitize_input(domain))
            return False

        email_list = [e.strip() for e in company.emails.split(';') if e.strip()]
        new_emails = [e for e in email_list if not self.db_service.is_email_collected(e)]

        if not new_emails and not company.phone:
            self.logger.debug("Nenhum dado novo", domain=self.logger._sanitize_input(domain))
            return False

        # Processar telefones
        telefones_data = []
        if company.phone:
            phone_list = [p.strip() for p in company.phone.split(';') if p.strip()]
            for phone in phone_list:
                telefones_data.append({
                    'original': phone,
                    'formatted': phone,  # Simplificado por agora
                    'ddd': phone[:2] if len(phone) >= 10 else '',
                    'tipo': 'CELULAR' if len(phone) == 11 else 'FIXO'
                })

        # Salvar no banco
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
            self.logger.info("Empresa salva no banco",
                             domain=self.logger._sanitize_input(domain),
                             emails_count=len(new_emails),
                             phones_count=len(telefones_data))

        return success
