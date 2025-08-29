"""
Camada de Aplicação - Serviço principal do robô coletor (refatorado)
"""
import random
import time
from typing import List

from config.settings import (
    START_HOUR, END_HOUR, OUT_OF_HOURS_WAIT_SECONDS, VISITED_JSON, 
    SEEN_EMAILS_JSON, OUTPUT_XLSX, BLACKLIST_HOSTS, MAX_EMAILS_PER_SITE,
    RESULTS_PER_TERM_LIMIT, SEARCH_DWELL, COMPLETE_MODE_THRESHOLD
)
from .user_config_service import UserConfigService
from ...domain.services.email_domain_service import (
    EmailCollectorInterface, WorkingHoursService, EmailValidationService
)
from ...domain.factories.search_term_factory import SearchTermFactory
from ...domain.models.search_term_model import SearchTermModel

from ...infrastructure.repositories.data_repository import JsonRepository, ExcelRepository
from ...infrastructure.scrapers.duckduckgo_scraper import DuckDuckGoScraper
from ...infrastructure.scrapers.google_scraper import GoogleScraper
from ...infrastructure.storage.data_storage import DataStorage
from ...infrastructure.drivers.web_driver import WebDriverManager


class EmailApplicationService(EmailCollectorInterface):
    """Serviço de aplicação do PythonSearchApp coletor de e-mails"""
    
    def __init__(self, ignore_working_hours=False):
        # Configurações do usuário
        self.search_engine = UserConfigService.get_search_engine()
        
        if UserConfigService.get_restart_option():
            DataStorage.clear_all_data()
        
        # Inicialização de componentes
        self.driver_manager = WebDriverManager()
        self._setup_scraper()
        self._setup_repositories()
        self._setup_services(ignore_working_hours)
        
        # Configuração final
        self.visited_domains = self.json_repo.load_visited_domains()
        self.seen_emails = self.json_repo.load_seen_emails()
        self.top_results_total = UserConfigService.get_processing_mode()
    
    def _setup_scraper(self):
        """Configura scraper baseado na escolha do usuário"""
        if self.search_engine == "GOOGLE":
            print("[INFO] Usando motor de busca: Google Chrome")
            self.scraper = GoogleScraper(None)
        else:
            print("[INFO] Usando motor de busca: DuckDuckGo")
            self.scraper = DuckDuckGoScraper(self.driver_manager)
    
    def _setup_repositories(self):
        """Configura repositórios de dados"""
        self.json_repo = JsonRepository(VISITED_JSON, SEEN_EMAILS_JSON)
        self.excel_repo = ExcelRepository(OUTPUT_XLSX)
    
    def _setup_services(self, ignore_working_hours):
        """Configura serviços de domínio"""
        self.working_hours = WorkingHoursService(START_HOUR, END_HOUR)
        self.ignore_working_hours = ignore_working_hours
        self.validation_service = EmailValidationService()
    
    def execute(self) -> bool:
        """Executa coleta completa de e-mails"""
        try:
            # ChromeDriver deve estar disponível via scripts de inicialização
            
            if not self.driver_manager.start_driver():
                print("[ERRO] Falha ao iniciar driver")
                return False
            
            if self.search_engine == "GOOGLE":
                self.scraper.driver = self.driver_manager.driver
            
            terms = SearchTermFactory.create_search_terms()
            return self.collect_emails(terms)
            
        finally:
            self.driver_manager.close_driver()
    
    def collect_emails(self, terms: List[SearchTermModel]) -> bool:
        """Coleta e-mails usando termos de busca"""
        total_saved = 0
        
        # Calcula total esperado
        if self.top_results_total > COMPLETE_MODE_THRESHOLD:
            total_expected_results = len(terms) * RESULTS_PER_TERM_LIMIT
        else:
            total_expected_results = len(terms) * self.top_results_total
        
        global_results_processed = 0
        
        for i, term in enumerate(terms, 1):
            # Verifica horário de trabalho
            if not self.ignore_working_hours:
                while not self.working_hours.is_working_time():
                    print(f"[PAUSA] Fora do horário ({START_HOUR}:00–{END_HOUR}:00). Recheco em {OUT_OF_HOURS_WAIT_SECONDS}s.")
                    time.sleep(OUT_OF_HOURS_WAIT_SECONDS)
            
            mode_text = "completo" if self.top_results_total > COMPLETE_MODE_THRESHOLD else f"lote ({self.top_results_total})"
            print(f"\n[TERMO {i}/{len(terms)}] {term.query} | modo: {mode_text}")
            
            if not self.scraper.search(term.query):
                print("  [ERRO] Busca falhou")
                continue
            
            term_saved = self._process_term_results(term, total_expected_results, global_results_processed)
            total_saved += term_saved
            global_results_processed += term_saved
            
            print(f"  => Termo concluído. Novas empresas: {term_saved}")
        
        print(f"\nFINALIZADO. Total de empresas novas: {total_saved}")
        print("[INFO] Processamento concluído. Encerrando PythonSearchApp...")
        return True
    
    def _process_term_results(self, term: SearchTermModel, total_expected: int, global_processed: int) -> int:
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
                
                if self.visited_domains.get(domain):
                    print(f"\n    [PULAR] Site já visitado: {domain}")
                    continue
                
                self.visited_domains[domain] = True
                print(f"\n    [VISITA] Acessando site: {domain} ({global_processed}/{total_expected} processado)")
                
                company = self.scraper.extract_company_data(link, MAX_EMAILS_PER_SITE)
                company.search_term = term.query
                
                if self._save_company_if_valid(company, domain):
                    term_saved += 1
                
                self._save_progress()
                time.sleep(random.uniform(*SEARCH_DWELL))
            
            # Próxima página
            if page < term.pages - 1 and results_processed < self.top_results_total:
                if hasattr(self.scraper, 'go_to_next_page'):
                    if not self.scraper.go_to_next_page():
                        print(f"    [INFO] Não há mais páginas para o termo '{term.query}'")
                        break
        
        return term_saved
    
    def _save_company_if_valid(self, company, domain: str) -> bool:
        """Salva empresa se tiver e-mails válidos e novos"""
        if not company.emails or not company.emails.strip():
            print(f"    [-] Sem e-mail válido: {domain}")
            return False
        
        email_list = [e.strip() for e in company.emails.split(';') if e.strip()]
        new_emails = [e for e in email_list if e not in self.seen_emails]
        
        if not new_emails:
            print(f"    [-] E-mails já coletados: {domain}")
            return False
        
        company.emails = ';'.join(new_emails) + ';'
        self.excel_repo.save_company(company)
        print(f"    [OK] Empresa salva em: {OUTPUT_XLSX}")
        
        for email in new_emails:
            self.seen_emails.add(email)
        
        return True
    
    def _save_progress(self):
        """Salva progresso atual"""
        self.json_repo.save_visited_domains(self.visited_domains)
        self.json_repo.save_seen_emails(self.seen_emails)