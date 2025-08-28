"""
Camada de Aplicação - Serviço principal do robô coletor
"""
import random
import time
import zipfile
from typing import List

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from config.settings import *
from ..domain.email_processor import (
    SearchTerm, EmailCollectorInterface,
    WorkingHoursService, SearchTermBuilder, EmailValidationService
)
from ..infrastructure.repositories.data_persistence import JsonRepository, ExcelRepository
from ..infrastructure.scrapers.duckduckgo_scraper import DuckDuckGoScraper
from ..infrastructure.scrapers.google_scraper import GoogleScraper
from ..infrastructure.web_driver import WebDriverManager


class EmailCollectorService(EmailCollectorInterface):
    """Serviço principal do PythonSearchApp coletor de e-mails"""
    
    # Constantes de configuração
    
    def __init__(self, ignore_working_hours=False):
        self.driver_manager = WebDriverManager()
        
        # Escolhe motor de busca
        self.search_engine = self._get_search_engine_option()
        
        # Verifica se deve reiniciar do zero
        if self._get_restart_option():
            self._clear_all_data()
        
        # Escolhe scraper baseado na seleção do usuário
        if self.search_engine == "GOOGLE":
            print("[INFO] Usando motor de busca: Google Chrome")
            self.scraper = GoogleScraper(None)  # Driver será definido depois
        else:
            print("[INFO] Usando motor de busca: DuckDuckGo")
            self.scraper = DuckDuckGoScraper(self.driver_manager)
        
        self.json_repo = JsonRepository(VISITED_JSON, SEEN_EMAILS_JSON)
        self.excel_repo = ExcelRepository(OUTPUT_XLSX)
        self.working_hours = WorkingHoursService(START_HOUR, END_HOUR)
        self.ignore_working_hours = ignore_working_hours
        self.term_builder = SearchTermBuilder()
        self.validation_service = EmailValidationService()
        
        # Recria repositórios após limpeza
        self.json_repo = JsonRepository(VISITED_JSON, SEEN_EMAILS_JSON)
        self.excel_repo = ExcelRepository(OUTPUT_XLSX)
        
        self.visited_domains = self.json_repo.load_visited_domains()
        self.seen_emails = self.json_repo.load_seen_emails()
        self.top_results_total = self._get_processing_mode()
    

    
    def _get_search_engine_option(self) -> str:
        """Obtém do usuário qual motor de busca usar"""
        while True:
            try:
                print("\n🔍 Escolha o motor de busca:")
                print("1. DuckDuckGo")
                print("2. Google Chrome")
                option = input("Digite sua opção (1/2 - padrão: 1): ").strip()
                
                if not option or option == '1':
                    return "DUCKDUCKGO"
                elif option == '2':
                    return "GOOGLE"
                else:
                    print("[ERRO] Digite '1' para DuckDuckGo ou '2' para Google Chrome")
            except:
                print("[ERRO] Entrada inválida")
    
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
        # Garante que pasta data existe
        os.makedirs(DATA_DIR, exist_ok=True)
        
        files_to_clear = [VISITED_JSON, SEEN_EMAILS_JSON, OUTPUT_XLSX]
        
        for file_path in files_to_clear:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"[INFO] Arquivo {file_path} removido")
            except Exception as e:
                print(f"[AVISO] Erro ao remover {file_path}: {e}")
        
        print("[OK] Dados anteriores limpos. Iniciando do zero...")
    

    
    def _get_processing_mode(self) -> int:
        """Obtém do usuário o modo de processamento"""
        while True:
            try:
                mode = input("\n🔍 Processamento em lote ou completo? (l/c - padrão: c): ").lower().strip()
                if not mode or mode == 'c':
                    return 999999  # Processamento completo
                elif mode == 'l':
                    # Pergunta quantidade para lote
                    while True:
                        try:
                            limit = input("Quantos resultados por termo? (padrão: 10): ")
                            if not limit.strip():
                                return 10
                            limit = int(limit)
                            if limit > 0:
                                return limit
                            else:
                                print("[ERRO] Digite um número maior que zero")
                        except ValueError:
                            print("[ERRO] Digite um número válido")
                else:
                    print("[ERRO] Digite 'l' para lote ou 'c' para completo")
            except:
                print("[ERRO] Entrada inválida")
    
    def _check_and_install_chromedriver(self) -> bool:
        """Verifica e instala ChromeDriver se necessário"""
        if os.path.exists("drivers/chromedriver.exe"):
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
                # Garante que pasta drivers existe
                os.makedirs('drivers', exist_ok=True)
                
                for file_info in zip_ref.filelist:
                    if file_info.filename.endswith('chromedriver.exe'):
                        with zip_ref.open(file_info) as source, open('drivers/chromedriver.exe', 'wb') as target:
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
            
            if not self.driver_manager.start_driver():
                print("[ERRO] Falha ao iniciar driver")
                return False
            
            # Define driver no scraper Google se necessário
            if self.search_engine == "GOOGLE":
                self.scraper.driver = self.driver_manager.driver
            
            # Lista única de termos de busca usando constantes
            search_terms = []
            
            # Verifica se é modo teste via configuração
            if IS_TEST_MODE:
                print("[INFO] Modo TESTE ativado via settings.py")
                # Modo teste - apenas alguns termos
                for base in BASE_BUSCA_TESTES:
                    search_terms.append(f"{base} {CIDADE_BASE} capital")
            else:
                print("[INFO] Modo PRODUÇÃO - processamento completo")
                # Modo produção - todos os termos
                # Capital
                for base in BASE_BUSCA:
                    search_terms.append(f"{base} {CIDADE_BASE} capital")

                # Zonas
                for base in BASE_BUSCA:
                    for zona in BASE_ZONAS:
                        search_terms.append(f"{base} {zona} {CIDADE_BASE}")

                # Bairros
                for base in BASE_BUSCA:
                    for bairro in BASE_BAIRROS:
                        search_terms.append(f"{base} {bairro} {CIDADE_BASE}")

                # Interior
                for base in BASE_BUSCA:
                    for cidade in CIDADES_INTERIOR:
                        search_terms.append(f"{base} {cidade} {UF_BASE}")

            # Converte para objetos SearchTerm
            terms = [SearchTerm(query=term, location=UF_BASE, category=CATEGORIA_BASE, pages=10) for term in search_terms]
            
            return self.collect_emails(terms)
            
        finally:
            self.driver_manager.close_driver()
    
    def collect_emails(self, terms: List[SearchTerm]) -> bool:
        """Coleta e-mails usando termos de busca"""
        total_saved = 0
        
        # Calcula total real de resultados esperados
        if self.top_results_total > 1000:  # Modo completo
            total_expected_results = len(terms) * RESULTS_PER_TERM_LIMIT
        else:  # Modo lote
            total_expected_results = len(terms) * self.top_results_total
        
        global_results_processed = 0  # Contador global
        
        for i, term in enumerate(terms, 1):
            # Verifica horário de trabalho apenas se não foi ignorado pelo usuário
            if not self.ignore_working_hours:
                while not self.working_hours.is_working_time():
                    print(f"[PAUSA] Fora do horário ({START_HOUR}:00–{END_HOUR}:00). Recheco em {OUT_OF_HOURS_WAIT_SECONDS}s.")
                    time.sleep(OUT_OF_HOURS_WAIT_SECONDS)
            
            mode_text = "completo" if self.top_results_total > 1000 else f"lote ({self.top_results_total})"
            print(f"\n[TERMO {i}/{len(terms)}] {term.query} | modo: {mode_text}")
            
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
                    global_results_processed += 1
                    domain = self.validation_service.extract_domain_from_url(link)
                    
                    if self.visited_domains.get(domain):
                        print(f"\n    [PULAR] Site já visitado: {domain}")
                        continue
                    
                    # Marca domínio como visitado ANTES de extrair dados
                    self.visited_domains[domain] = True
                    print(f"\n    [VISITA] Acessando site: {domain} ({global_results_processed}/{total_expected_results} processado)")
                    
                    company = self.scraper.extract_company_data(link, MAX_EMAILS_PER_SITE)
                    company.search_term = term.query  # Adiciona termo de busca
                    
                    # Só processa se há e-mails válidos na string
                    if company.emails and company.emails.strip():
                        # Separa e-mails da string para verificar se já foram vistos
                        email_list = [e.strip() for e in company.emails.split(';') if e.strip()]
                        new_emails = [e for e in email_list if e not in self.seen_emails]
                        
                        if new_emails:
                            # Reconstrói string apenas com e-mails novos
                            company.emails = ';'.join(new_emails)
                            self.excel_repo.save_company(company)
                            print(f"    [OK] Empresa salva em: {OUTPUT_XLSX}")
                            
                            # Atualiza controle de e-mails
                            for email in new_emails:
                                self.seen_emails.add(email)
                            
                            term_saved += 1
                            total_saved += 1
                        else:
                            print(f"    [-] E-mails já coletados: {domain}")
                    else:
                        print(f"    [-] Sem e-mail válido: {domain}")
                    
                    # Salva progresso sempre
                    self.json_repo.save_visited_domains(self.visited_domains)
                    self.json_repo.save_seen_emails(self.seen_emails)
                    
                    time.sleep(random.uniform(*SEARCH_DWELL))
                
                # Vai para próxima página se ainda há páginas para processar
                if page < term.pages - 1 and results_processed < self.top_results_total:
                    if hasattr(self.scraper, 'go_to_next_page'):
                        if not self.scraper.go_to_next_page():
                            print(f"    [INFO] Não há mais páginas para o termo '{term.query}'")
                            break
                    else:
                        # Fallback para scrapers sem go_to_next_page
                        try:
                            self.driver_manager.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
                            time.sleep(random.uniform(1.0, 1.6))
                        except:
                            pass
            
            print(f"  => Termo concluído. Novas empresas: {term_saved}")
        
        print(f"\nFINALIZADO. Total de empresas novas: {total_saved}")
        print("[INFO] Processamento concluído. Encerrando PythonSearchApp...")
        return True