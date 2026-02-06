"""
Collection Executor Service - Núcleo de execução de coletas
Responsável pela lógica central de coleta de dados de empresas
"""
import random
import time
from typing import Dict, Callable, Optional

from config.settings import (
    BLACKLIST_HOSTS, MAX_EMAILS_PER_SITE
)
from src.application.services.database_application_service import DatabaseApplicationService
from src.domain.services.email_domain_service import EmailValidationService
from src.infrastructure.config.config_manager import ConfigManager
from src.infrastructure.drivers.playwright_manager import PlaywrightManager
from src.infrastructure.logging.structured_logger import StructuredLogger


class CollectionExecutorService:
    """
    Service executor de coletas - Núcleo da lógica de coleta

    Este service contém toda a lógica de:
    - Inicialização do Playwright
    - Configuração de scrapers
    - Busca e coleta de links
    - Extração de dados de empresas
    - Salvamento no banco
    """

    def __init__(self):
        self.logger = StructuredLogger("collection_executor")
        self.config = ConfigManager()
        self.db_service = DatabaseApplicationService()
        self.validation_service = EmailValidationService()

    def execute_collection_for_term(
        self,
        term: str,
        browser: str = 'CHROME',
        engine: str = 'GOOGLE',
        headless: bool = True,
        search_mode: str = 'FAST',  # 🆕 'FAST' ou 'DEEP'
        progress_callback: Optional[Callable] = None,
        should_stop_callback: Optional[Callable] = None,
        db_lock = None
    ) -> Dict:
        """
        Executa coleta para um único termo

        Args:
            term: Termo de busca
            browser: Browser (CHROME ou BRAVE)
            engine: Engine (GOOGLE ou DUCKDUCKGO)
            headless: Modo headless
            search_mode: Modo de busca ('FAST' ou 'DEEP')
            progress_callback: Callback de progresso
            should_stop_callback: Callback para verificar parada
            db_lock: Lock para thread-safety

        Returns:
            Dict com resultado da coleta
        """
        try:
            # 🎯 LOG INICIAL - Header
            print(f"\n{'='*80}")
            print(f"🔍 INICIANDO COLETA | Termo: '{term}'")
            print(f"{'='*80}")
            print(f"  Engine: {engine} | Browser: {browser} | Headless: {headless}")
            print(f"{'='*80}\n")

            # 🎭 PASSO 1: Playwright
            print(f"[PASSO 1/5] 🎭 Inicializando Playwright")
            print(f"  → Browser: {browser}")
            print(f"  → Headless: {headless}")

            playwright_manager = PlaywrightManager(
                headless=headless,
                browser_type=browser
            )
            playwright_manager.start()
            page = playwright_manager.get_page()

            if not page:
                print(f"  ❌ ERRO: Falha ao obter página do Playwright")
                return {'success': False, 'error': 'Falha ao iniciar Playwright'}

            print(f"  ✅ Playwright iniciado com sucesso")
            print()

            # 🔧 PASSO 2: Configurar Scraper
            print(f"[PASSO 2/5] 🔧 Configurando Scraper")

            # 🆕 Usar search_mode recebido como parâmetro
            use_intelligent = (search_mode == 'DEEP')
            search_mode_label = "Deep Search" if use_intelligent else "Fast Search"
            print(f"  🎯 Modo: {search_mode_label} (escolhido via UI)")

            # Escolher scraper apropriado baseado no search_mode
            if engine == "GOOGLE":
                if use_intelligent:
                    # Deep Search - com classificação inteligente
                    from ..engines.google.deep_search_google_scraper import DeepSearchGoogleScraper
                    scraper = DeepSearchGoogleScraper(page)
                    print(f"  ✅ Google Deep Search Scraper configurado")
                else:
                    # Fast Search - sem classificação
                    from ..engines.google.fast_search_google_scraper import FastSearchGoogleScraper
                    scraper = FastSearchGoogleScraper(page)
                    print(f"  ✅ Google Fast Search Scraper configurado")
            else:  # DUCKDUCKGO
                if use_intelligent:
                    # Deep Search - com classificação inteligente
                    from ..engines.duckduckgo.deep_search_duckduckgo_scraper import DeepSearchDuckDuckGoScraper
                    scraper = DeepSearchDuckDuckGoScraper(page)
                    print(f"  ✅ DuckDuckGo Deep Search Scraper configurado")
                else:
                    # Fast Search - sem classificação
                    from ..engines.duckduckgo.fast_search_duckduckgo_scraper import FastSearchDuckDuckGoScraper
                    scraper = FastSearchDuckDuckGoScraper(page)
                    print(f"  ✅ DuckDuckGo Fast Search Scraper configurado")

            print()

            try:
                # 🔍 PASSO 3: Executar Busca
                print(f"[PASSO 3/5] 🔍 Executando Busca no {engine}")
                if progress_callback:
                    progress_callback(5, f"Buscando: {term}")

                search_result = scraper.search(term)
                if not search_result:
                    print(f"  ❌ Busca falhou")

                    return {'success': False, 'error': 'Busca falhou'}

                print(f"  ✅ Busca concluída")
                print()

                if progress_callback:
                    progress_callback(15, "Busca concluída, coletando resultados...")

                # 📋 Obter termo do banco
                print(f"[PASSO 4/5] 📋 Preparando Coleta")
                if db_lock:
                    with db_lock:
                        terms_data = [t for t in self.db_service.get_search_terms() if t['termo'] == term]
                else:
                    terms_data = [t for t in self.db_service.get_search_terms() if t['termo'] == term]

                if not terms_data:
                    print(f"  ❌ Termo não encontrado no banco")
                    return {'success': False, 'error': 'Termo não encontrado no banco'}

                term_data = terms_data[0]
                termo_id = term_data['id']
                print(f"  ✅ Termo ID: {termo_id}")
                print()

                # 📊 Processar resultados
                print(f"[PASSO 5/5] 📊 Coletando Dados")
                companies_found = 0
                total_links = 0

                # Processar páginas
                for page_num in range(3):
                    print(f"\n  📄 Página {page_num + 1}/3")

                    # Verificar se deve parar
                    if should_stop_callback and should_stop_callback():
                        print(f"    ⏹️  Parada solicitada pelo usuário")
                        if progress_callback:
                            progress_callback(100, "Parado pelo usuário")
                        break

                    links = scraper.get_result_links(BLACKLIST_HOSTS)
                    if not links:
                        print(f"    ⚠️  Nenhum link encontrado")
                        break

                    total_links += len(links)
                    print(f"    🔗 {len(links)} links coletados")

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
                            print(f"    ⏭️  Pulando {domain} (já visitado)")
                            continue

                        # Extrair dados (o scraper já faz log detalhado)
                        company = scraper.extract_company_data(link, MAX_EMAILS_PER_SITE)
                        company.search_term = term

                        # Salvar no banco (thread-safe com lock)
                        saved = False
                        if db_lock:
                            with db_lock:
                                saved = self._save_company_to_database(company, domain, termo_id, engine)
                        else:
                            saved = self._save_company_to_database(company, domain, termo_id, engine)

                        if saved:
                            companies_found += 1
                            print(f"      ✅ Empresa salva ({companies_found} total)")

                        # Pequeno delay
                        time.sleep(random.uniform(0.1, 0.3))

                    # Próxima página
                    if page_num < 2:
                        if hasattr(scraper, 'go_to_next_page'):
                            print(f"    ➡️  Indo para próxima página...")
                            if not scraper.go_to_next_page():
                                print(f"    ⚠️  Não há mais páginas")
                                break

                # ✅ Finalização
                print(f"\n{'='*80}")
                print(f"✅ COLETA CONCLUÍDA")
                print(f"{'='*80}")
                print(f"  📊 Estatísticas:")
                print(f"    • Empresas encontradas: {companies_found}")
                print(f"    • Links processados: {total_links}")
                print(f"    • Termo: {term}")
                print(f"{'='*80}\n")

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
                print(f"  🔒 Playwright finalizado\n")

        except Exception as e:
            print(f"\n❌ ERRO NA COLETA: {str(e)}\n")
            self.logger.error(f"Erro ao processar termo '{term}': {e}")
            return {'success': False, 'error': str(e)}

    def _save_company_to_database(self, company, domain: str, termo_id: int, engine: str = 'GOOGLE') -> bool:
        """
        Salva empresa no banco de dados

        SEMPRE salva quando visita um site, diferenciando:
        - Status COLETADO: Se encontrou email, telefone ou endereço
        - Status NAO_COLETADO: Se visitou mas não encontrou dados

        Args:
            company: Dados da empresa coletada
            domain: Domínio da empresa
            termo_id: ID do termo de busca
            engine: Motor de busca usado (GOOGLE ou DUCKDUCKGO)
        """
        try:
            # Converter emails de string para lista
            emails_list = [e.strip() for e in company.emails.split(';') if e.strip()] if company.emails else []

            # Converter telefones de string para lista
            phones_list = [p.strip() for p in company.phone.split(';') if p.strip()] if company.phone else []

            # Verificar se tem endereço
            has_address = bool(company.address and company.address.strip())

            # ✅ SEMPRE SALVA quando visita o site
            # Status será determinado pelo banco baseado nos dados encontrados
            success = self.db_service.save_company_data(
                termo_id=termo_id,
                site_url=company.url,
                domain=domain,
                motor_busca=engine,
                emails=emails_list,
                telefones=phones_list,
                nome_empresa=company.name or domain,
                html_content=company.html_content or ''
            )

            # Log diferenciado
            if emails_list or phones_list or has_address:
                status = "✅ COLETADO"
                details = []
                if emails_list:
                    details.append(f"{len(emails_list)} email(s)")
                if phones_list:
                    details.append(f"{len(phones_list)} telefone(s)")
                if has_address:
                    details.append("endereço")
                print(f"      {status}: {', '.join(details)}")
            else:
                print(f"      ⚠️  NAO_COLETADO: Visitado mas sem dados")

            return success

        except Exception as e:
            self.logger.error(f"Erro ao salvar empresa: {e}")
            return False
