"""
Camada de Aplicação - Serviço principal do robô coletor
"""
import time
import random
import os
import requests
import zipfile
from typing import List
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from ..domain.email_processor import (
    Company, SearchTerm, EmailCollectorInterface, 
    WorkingHoursService, SearchTermBuilder, EmailValidationService
)
from ..infrastructure.web_driver import WebDriverManager
from ..infrastructure.scrapers.duckduckgo_scraper import DuckDuckGoScraper
from ..infrastructure.repositories.data_persistence import JsonRepository, ExcelRepository
from config.settings import *


class EmailCollectorService(EmailCollectorInterface):
    """Serviço principal do robô coletor de e-mails"""
    
    # Constantes de configuração
    
    def __init__(self):
        self.driver_manager = WebDriverManager()
        self.scraper = DuckDuckGoScraper(self.driver_manager)
        self.json_repo = JsonRepository(VISITED_JSON, SEEN_EMAILS_JSON)
        self.excel_repo = ExcelRepository(OUTPUT_XLSX)
        self.working_hours = WorkingHoursService(START_HOUR, END_HOUR)
        self.term_builder = SearchTermBuilder()
        self.validation_service = EmailValidationService()
        
        # Verifica se deve reiniciar do zero
        if self._get_restart_option():
            self._clear_all_data()
        
        self.visited_domains = self.json_repo.load_visited_domains()
        self.seen_emails = self.json_repo.load_seen_emails()
        self.headless_mode = self._get_execution_mode()
        self.top_results_total = self._get_results_limit()
    

    
    def _get_restart_option(self) -> bool:
        """Obtém do usuário se deve reiniciar do zero"""
        while True:
            try:
                option = input("\n🔄 Reiniciar busca do zero? (s/n - padrão: n): ").lower().strip()
                if not option or option == 'n':
                    return False  # Continuar
                elif option == 's':
                    return True   # Reiniciar
                else:
                    print("[ERRO] Digite 's' para reiniciar ou 'n' para continuar")
            except:
                print("[ERRO] Entrada inválida")
    
    def _clear_all_data(self):
        """Limpa todos os arquivos de dados"""
        files_to_clear = [VISITED_JSON, SEEN_EMAILS_JSON, OUTPUT_XLSX, OUTPUT_XLSX.replace('.xlsx', '.csv')]
        
        for file_path in files_to_clear:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"[INFO] Arquivo {file_path} removido")
            except Exception as e:
                print(f"[AVISO] Erro ao remover {file_path}: {e}")
        
        print("[OK] Dados anteriores limpos. Iniciando do zero...")
    
    def _get_execution_mode(self) -> bool:
        """Obtém do usuário o modo de execução"""
        while True:
            try:
                mode = input("\n🕰️ Executar em segundo plano? (s/n - padrão: n): ").lower().strip()
                if not mode or mode == 'n':
                    return False  # Visível
                elif mode == 's':
                    return True   # Headless
                else:
                    print("[ERRO] Digite 's' para segundo plano ou 'n' para visível")
            except:
                print("[ERRO] Entrada inválida")
    
    def _get_results_limit(self) -> int:
        """Obtém do usuário o limite de resultados por termo"""
        while True:
            try:
                limit = input("\n🔍 Quantos resultados processar por termo de busca? (padrão: 50): ")
                if not limit.strip():
                    return 50
                limit = int(limit)
                if limit > 0:
                    return limit
                else:
                    print("[ERRO] Digite um número maior que zero")
            except ValueError:
                print("[ERRO] Digite um número válido")
    
    def _check_and_install_chromedriver(self) -> bool:
        """Verifica e instala ChromeDriver se necessário"""
        if os.path.exists("chromedriver.exe"):
            return True
        
        print("[INFO] ChromeDriver não encontrado. Baixando automaticamente...")
        
        try:
            # Detecta versão do Chrome
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
            version, _ = winreg.QueryValueEx(key, "version")
            chrome_version = version.split('.')[0]
        except:
            chrome_version = "119"  # Versão padrão
        
        try:
            # Busca versão compatível
            api_url = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
            response = requests.get(api_url, timeout=10)
            data = response.json()
            
            download_url = None
            for version_info in reversed(data['versions']):
                if version_info['version'].startswith(chrome_version):
                    for download in version_info['downloads'].get('chromedriver', []):
                        if download['platform'] == 'win64':
                            download_url = download['url']
                            break
                    if download_url:
                        break
            
            if not download_url:
                print("[ERRO] Não foi possível encontrar versão compatível do ChromeDriver")
                return False
            
            # Baixa e extrai
            print("[INFO] Baixando ChromeDriver...")
            response = requests.get(download_url, timeout=30)
            
            with open("chromedriver.zip", 'wb') as f:
                f.write(response.content)
            
            with zipfile.ZipFile("chromedriver.zip", 'r') as zip_ref:
                for file_info in zip_ref.filelist:
                    if file_info.filename.endswith('chromedriver.exe'):
                        with zip_ref.open(file_info) as source, open('chromedriver.exe', 'wb') as target:
                            target.write(source.read())
                        break
            
            os.remove("chromedriver.zip")
            print("[OK] ChromeDriver instalado com sucesso")
            return True
            
        except Exception as e:
            print(f"[ERRO] Falha ao baixar ChromeDriver: {e}")
            return False
    
    def execute(self) -> bool:
        """Executa coleta completa de e-mails"""
        try:
            # Verifica e instala ChromeDriver se necessário
            if not self._check_and_install_chromedriver():
                print("[ERRO] ChromeDriver não disponível")
                return False
            
            if not self.driver_manager.start_driver(self.headless_mode):
                print("[ERRO] Falha ao iniciar driver")
                return False
            
            # Lista única de termos de busca usando constantes
            search_terms = []
            
            # # Capital
            # for base in BASE_ELEVADORES:
            #     search_terms.append(f"{base} São Paulo capital")
            #
            # # Bairros
            # for base in BASE_ELEVADORES:
            #     for bairro in BAIRROS_SP:
            #         search_terms.append(f"{base} {bairro} São Paulo")
            #
            # # Interior
            # for base in BASE_ELEVADORES:
            #     for cidade in CIDADES_INTERIOR:
            #         search_terms.append(f"{base} {cidade} SP")

            for base in BASE_SEMINOVOS:
                search_terms.append(f"{base} São Paulo capital")

            # Converte para objetos SearchTerm
            terms = [SearchTerm(query=term, location=SEARCH_LOCATION, category=SEARCH_CATEGORY, pages=10) for term in search_terms]
            
            return self.collect_emails(terms)
            
        finally:
            self.driver_manager.close_driver()
    
    def collect_emails(self, terms: List[SearchTerm]) -> bool:
        """Coleta e-mails usando termos de busca"""
        total_saved = 0
        
        for i, term in enumerate(terms, 1):
            # Verifica horário de trabalho
            while not self.working_hours.is_working_time():
                print(f"[PAUSA] Fora do horário ({START_HOUR}:00–{END_HOUR}:00). Recheco em {TIME_BETWEEN_OUT_OF_HOURS}s.")
                time.sleep(TIME_BETWEEN_OUT_OF_HOURS)
            
            print(f"\n[TERMO {i}/{len(terms)}] {term.query} | limite: {self.top_results_total} resultados")
            
            if not self.scraper.search(term.query):
                print("  [ERRO] Busca falhou")
                continue
            
            term_saved = 0
            results_processed = 0  # Contador de resultados processados
            
            for page in range(term.pages):
                # Para se já processou o limite de resultados
                if results_processed >= self.top_results_total:
                    break
                    
                links = self.scraper.get_result_links(BLACKLIST_HOSTS)
                if not links:
                    break
                
                for link in links:
                    # Para se já processou o limite de resultados
                    if results_processed >= self.top_results_total:
                        break
                        
                    results_processed += 1
                    domain = self.validation_service.extract_domain_from_url(link)
                    
                    if self.visited_domains.get(domain):
                        continue
                    
                    company = self.scraper.extract_company_data(link, MAX_EMAILS_PER_SITE)
                    company.search_term = term.query  # Adiciona termo de busca
                    
                    if company.emails:
                        # Filtra e-mails já vistos
                        new_emails = [e for e in company.emails if e not in self.seen_emails]
                        
                        if new_emails:
                            company.emails = new_emails
                            self.excel_repo.save_company(company)
                            
                            # Atualiza controles
                            self.visited_domains[domain] = True
                            for email in new_emails:
                                self.seen_emails.add(email)
                            
                            term_saved += 1
                            total_saved += 1
                            print(f"    [+] {company.name} | {new_emails}")
                    else:
                        print(f"    [-] Sem e-mail válido: {domain}")
                    
                    # Salva progresso
                    self.json_repo.save_visited_domains(self.visited_domains)
                    self.json_repo.save_seen_emails(self.seen_emails)
                    
                    time.sleep(random.uniform(*SEARCH_DWELL))
                
                # Scroll na página de resultados
                try:
                    self.driver_manager.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
                    time.sleep(random.uniform(1.0, 1.6))
                except:
                    pass
            
            print(f"  => Termo concluído. Novas empresas: {term_saved}")
        
        print(f"\nFINALIZADO. Total de empresas novas: {total_saved}")
        print("[INFO] Processamento concluído. Encerrando robô...")
        return True