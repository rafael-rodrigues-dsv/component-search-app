"""
Google Deep Search Scraper - Sistema Inteligente
Scraper avançado com classificação de sites e extração inteligente
"""
from typing import List
from src.domain.scrapers.orchestrator.scraper_coordinator import ScraperCoordinator
from src.domain.scrapers.utils.scraper_logger import ScraperLogger
from src.infrastructure.scrapers.switcher.yaml_config_loader import get_scraper_config
from src.domain.models.company_model import CompanyModel


class DeepSearchGoogleScraper:
    """
    Google Deep Search Scraper - Sistema Inteligente

    Características:
    - Fast Path prioritário
    - Classificação automática de sites
    - Budget controlado
    - Logging transparente e cascateado
    """

    def __init__(self, page):
        self.page = page
        self.logger = ScraperLogger('GOOGLE_V2')
        self.config = get_scraper_config()
        # 🆕 Passar headless do config para coordinator
        self.coordinator = ScraperCoordinator(headless=self.config.headless)

    def search(self, term: str, max_results: int = 50) -> bool:
        """
        Busca no Google (compatível com interface legada)

        Args:
            term: Termo de busca
            max_results: Máximo de resultados

        Returns:
            bool: True se busca foi bem-sucedida
        """
        self.logger.log_step(f"Iniciando busca: '{term}'", 'search')

        try:
            # Reutilizar lógica de busca do scraper legado
            result = self._execute_google_search(term)

            if result:
                self.logger.log_step_end("Busca concluída", 'success')
            else:
                self.logger.log_step_end("Busca falhou", 'error')

            return result
        except Exception as e:
            self.logger.log_step_end(f"Erro: {str(e)[:40]}", 'error')
            return False
        finally:
            self.logger.reset_indent()

    def _execute_google_search(self, term: str) -> bool:
        """Executa busca no Google (lógica legada mantida)"""
        try:
            import time
            import random

            # Detectar CAPTCHA antes de começar
            if '/sorry/' in self.page.url or 'captcha' in self.page.url.lower():
                self.logger.log('warning', "CAPTCHA detectado! Aguardando 30 segundos...")
                time.sleep(30)

            self.logger.log('web', "Acessando google.com...")
            self.logger.indent()

            # ...existing code for delays config...
            from src.infrastructure.config.config_manager import ConfigManager
            cfg = ConfigManager()
            page_load_min = cfg.get_config_value('search.delays.google.page_load_min', 0.05)
            page_load_max = cfg.get_config_value('search.delays.google.page_load_max', 0.15)
            search_dwell_min = cfg.get_config_value('search.delays.google.search_dwell_min', 0.05)
            search_dwell_max = cfg.get_config_value('search.delays.google.search_dwell_max', 0.1)

            self.page.goto("https://www.google.com", wait_until='domcontentloaded', timeout=30000)

            # Comportamento humano: scroll e movimentos
            delay = random.uniform(page_load_min, page_load_max)
            self.logger.log('clock', f"Aguardando {delay:.2f}s (page_load)...")
            time.sleep(delay)

            # Scroll aleatório
            self.page.mouse.wheel(0, random.randint(100, 300))
            time.sleep(random.uniform(0.3, 0.6))

            self.logger.log('success', "Página carregada")

            self.logger.log('keyboard', "Digitando termo de busca...")

            # Tentar múltiplos seletores
            search_selectors = [
                'input[name="q"]',
                'textarea[name="q"]',
                '#APjFqb',
                'textarea.gLFyf'
            ]

            typed = False
            for selector in search_selectors:
                try:
                    # Simular clique e digitação humana
                    self.page.click(selector, timeout=5000)
                    time.sleep(random.uniform(0.2, 0.4))

                    # Digitar com delay entre caracteres
                    self.page.type(selector, term, delay=random.randint(50, 150))

                    delay = random.uniform(search_dwell_min, search_dwell_max)
                    self.logger.log('clock', f"Aguardando {delay:.2f}s (search_dwell)...")
                    time.sleep(delay)

                    self.page.press(selector, 'Enter')
                    typed = True
                    self.logger.log('success', f"Digitado com sucesso")
                    break
                except:
                    continue

            if not typed:
                self.logger.dedent()
                self.logger.log('error', "Campo de busca não encontrado")
                return False

            # Aguardar navegação e resultados carregarem
            self.logger.log('clock', "Aguardando resultados...")
            time.sleep(random.uniform(2.0, 3.0))

            # Verificar se URL mudou (indica que busca foi executada)
            current_url = self.page.url

            # Verificar CAPTCHA
            if '/sorry/' in current_url or 'captcha' in current_url.lower():
                self.logger.dedent()
                self.logger.log('error', "🚫 CAPTCHA detectado!")
                self.logger.log('warning', "💡 Use modo NÃO-HEADLESS (Mostrar Navegador: Sim)")
                return False

            # Verificar se chegou na página de resultados
            if '/search?' in current_url or '/search#' in current_url:
                self.logger.log('success', "Resultados carregados")
                self.logger.dedent()
                return True
            else:
                self.logger.dedent()
                self.logger.log('error', "URL não mudou - busca pode ter falhado")
                return False



        except Exception as e:
            self.logger.dedent()
            self.logger.log('error', f"Erro na busca: {str(e)[:50]}")
            return False

    def get_result_links(self, blacklist_hosts: List[str]) -> List[str]:
        """
        Extrai links dos resultados (compatível com interface legada)

        Args:
            blacklist_hosts: Lista de hosts para ignorar

        Returns:
            List[str]: URLs dos resultados
        """
        self.logger.log('link', "Coletando links...")
        self.logger.indent()

        try:
            # Aguardar elementos de resultado carregarem (CRÍTICO!)
            try:
                self.page.wait_for_selector('div#search', timeout=10000)
            except:
                pass

            # Scroll na página
            self.page.mouse.wheel(0, 1000)
            import time, random
            time.sleep(random.uniform(0.5, 1.0))
            time.sleep(1.0)

            # Extrair todos os links <a>
            links = self.page.query_selector_all('a')
            self.logger.log('info', f"Total de links na página: {len(links)}")

            urls = []
            filtered_count = 0

            for link in links:
                try:
                    href = link.get_attribute('href')
                    if not href:
                        continue

                    # Filtrar apenas URLs válidas
                    if not href.startswith('http'):
                        continue

                    # Ignorar links do Google
                    if 'google.com' in href or 'google.' in href:
                        filtered_count += 1
                        continue

                    # Extrair domínio para verificar blacklist
                    try:
                        domain = href.split('/')[2].lower() if '/' in href else ''
                    except:
                        continue

                    # Verificar blacklist
                    if domain and any(host in domain for host in blacklist_hosts):
                        filtered_count += 1
                        continue

                    # Adicionar se não estiver duplicado
                    if href not in urls:
                        urls.append(href)

                except:
                    continue

            self.logger.log('success', f"{len(urls)} links coletados")
            if filtered_count > 0:
                self.logger.log('warning', f"{filtered_count} links filtrados (blacklist)")
            self.logger.dedent()
            return urls

        except Exception as e:
            self.logger.dedent()
            self.logger.log('error', f"Erro coletando links: {str(e)[:50]}")
            return []

    def extract_company_data(self, url: str, max_emails: int) -> CompanyModel:
        """
        NOVO SISTEMA DE EXTRAÇÃO

        Interface compatível com scraper legado

        Args:
            url: URL para extrair
            max_emails: Máximo de emails

        Returns:
            CompanyModel: Dados da empresa
        """
        self.logger.log_step(f"Extraindo dados de: {url[:60]}...", 'target')

        try:
            # Usar ScraperCoordinator (novo sistema)
            self.logger.log('robot', "Executando sistema inteligente...")
            self.logger.indent()

            result = self.coordinator.scrape(url)

            self.logger.dedent()

            if result.success:
                # Converter para CompanyModel (formato legado)
                company = self._convert_to_company_model(result.data, url)

                # Log resumo
                email_count = len(company.emails.split(',')) if company.emails else 0
                phone_count = len(company.phone.split(',')) if company.phone else 0

                self.logger.log('chart', f"Resultados: {email_count} email(s), {phone_count} telefone(s)")
                self.logger.log_step_end("Extração concluída", 'success')

                return company
            else:
                # Retornar vazio (compatível com legado)
                self.logger.log_step_end("Nenhum dado extraído", 'warning')
                return CompanyModel(
                    name="",
                    emails="",
                    domain=self._extract_domain(url),
                    url=url,
                    address="",
                    phone="",
                    html_content=""
                )

        except Exception as e:
            self.logger.log('error', f"Erro: {str(e)[:50]}")
            return CompanyModel(
                name="",
                emails="",
                domain=self._extract_domain(url),
                url=url,
                address="",
                phone="",
                html_content=""
            )

    def _convert_to_company_model(self, extraction_result, url: str) -> CompanyModel:
        """
        Converte resultado do novo sistema para formato legado

        Args:
            extraction_result: ExtractionResult do novo sistema
            url: URL

        Returns:
            CompanyModel
        """
        return CompanyModel(
            name=extraction_result.company_name or self._extract_domain(url),
            emails=';'.join(extraction_result.emails) + ';' if extraction_result.emails else '',
            domain=extraction_result.domain or self._extract_domain(url),
            url=url,
            address=extraction_result.address or "",
            phone=';'.join(extraction_result.phones) + ';' if extraction_result.phones else '',
            html_content=extraction_result.html_content or ""
        )

    def _extract_domain(self, url: str) -> str:
        """Extrai domínio da URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return url.split('/')[2] if '/' in url else url
