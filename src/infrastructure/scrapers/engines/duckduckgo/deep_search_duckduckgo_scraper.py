"""
DuckDuckGo Deep Search Scraper - Sistema Inteligente
Scraper avançado com classificação de sites e extração inteligente
"""
from typing import List
from playwright.sync_api import Page
from src.domain.scrapers.orchestrator.scraper_coordinator import ScraperCoordinator
from src.domain.scrapers.utils.scraper_logger import ScraperLogger
from src.infrastructure.scrapers.switcher.yaml_config_loader import get_scraper_config
from src.domain.models.company_model import CompanyModel


class DeepSearchDuckDuckGoScraper:
    """
    DuckDuckGo Deep Search Scraper - Sistema Inteligente

    Interface compatível com scraper legado
    Inclui classificação automática e extração inteligente
    """

    def __init__(self, page: Page):
        self.page = page
        self.logger = ScraperLogger('DUCKDUCKGO_V2')
        self.config = get_scraper_config()
        # 🆕 Passar headless do config para coordinator
        self.coordinator = ScraperCoordinator(headless=self.config.headless)

    def search(self, search_term: str, num_results: int = 50) -> bool:
        """
        Busca no DuckDuckGo (compatível com interface legada)

        Args:
            search_term: Termo de busca
            num_results: Número de resultados

        Returns:
            bool: True se busca bem-sucedida
        """
        self.logger.log('search', f"Iniciando busca: '{search_term}'")

        # Reutilizar lógica de busca do scraper legado
        return self._execute_duckduckgo_search(search_term)

    def _execute_duckduckgo_search(self, search_term: str) -> bool:
        """Executa busca no DuckDuckGo (lógica legada mantida)"""
        try:
            import time
            import random
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

            self.logger.log('web', "Acessando duckduckgo.com...")
            self.logger.indent()

            # ✅ Respeitar delays do application.yaml
            from src.infrastructure.config.config_manager import ConfigManager
            cfg = ConfigManager()
            page_load_min = cfg.get_config_value('search.delays.duckduckgo.page_load_min', 0.03)
            page_load_max = cfg.get_config_value('search.delays.duckduckgo.page_load_max', 0.1)
            search_dwell_min = cfg.get_config_value('search.delays.duckduckgo.search_dwell_min', 0.03)
            search_dwell_max = cfg.get_config_value('search.delays.duckduckgo.search_dwell_max', 0.08)

            self.page.goto("https://duckduckgo.com/", wait_until='domcontentloaded', timeout=10000)

            # ✅ Delay após carregar página
            delay = random.uniform(page_load_min, page_load_max)
            self.logger.log('clock', f"Aguardando {delay:.2f}s (page_load)...")
            time.sleep(delay)

            self.logger.log('success', "Página carregada")

            # Scroll aleatório (comportamento humano)
            self.page.mouse.wheel(0, random.randint(50, 150))
            time.sleep(random.uniform(0.3, 0.6))

            self.logger.log('keyboard', "Digitando termo de busca...")

            # Tentar múltiplos seletores para o campo de busca
            search_selectors = [
                '#searchbox_input',
                'input[name="q"]',
                'input[type="text"]',
                '#search_form_input'
            ]

            typed = False
            for selector in search_selectors:
                try:
                    # Comportamento humano: clicar e digitar letra por letra
                    self.page.click(selector, timeout=5000)
                    time.sleep(random.uniform(0.2, 0.4))

                    # Digitar com delay entre caracteres
                    self.page.type(selector, search_term, delay=random.randint(40, 120))

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

            self.logger.log('clock', "Aguardando resultados...")

            # Tentar múltiplos seletores de resultados
            result_selectors = [
                '[data-testid="result"]',  # Seletor principal (novo)
                'article[data-testid="result"]',  # Variação com article
                '.result',  # Classe antiga
                '#links .result',  # Container de links
                'div[data-nrn="result"]'  # Outro padrão possível
            ]

            results_loaded = False
            for selector in result_selectors:
                try:
                    self.logger.log('search', f"Tentando selector: {selector}")
                    self.page.wait_for_selector(selector, timeout=5000)
                    self.logger.log('success', f"Resultados encontrados com: {selector}")
                    results_loaded = True
                    break
                except Exception:
                    continue

            if not results_loaded:
                # Última tentativa: verificar se a URL mudou
                current_url = self.page.url
                if '?q=' in current_url or '/search' in current_url:
                    self.logger.log('warning', "Resultados não detectados mas URL mudou, prosseguindo...")
                    time.sleep(2)
                    results_loaded = True
                else:
                    self.logger.dedent()
                    self.logger.log('error', "Nenhum resultado encontrado")
                    return False

            self.logger.log('success', "Busca concluída")
            self.logger.dedent()
            return True

        except Exception as e:
            self.logger.dedent()
            self.logger.log('error', f"Erro na busca: {str(e)[:50]}")
            return False

    def get_result_links(self, blacklist_hosts: List[str]) -> List[str]:
        """
        Extrai links dos resultados (compatível)

        Args:
            blacklist_hosts: Hosts para ignorar

        Returns:
            List[str]: URLs
        """
        self.logger.log('link', "Coletando links...")
        self.logger.indent()

        try:
            import time
            import random
            from src.infrastructure.config.delay_config import get_scraper_delays

            delays = get_scraper_delays("DUCKDUCKGO")

            self.page.mouse.wheel(0, 1500)
            time.sleep(random.uniform(*delays["scroll"]))

            self.page.wait_for_selector('[data-testid="result"]', timeout=5000)

            cards = self.page.locator('[data-testid="result"]').all()
            urls = []
            filtered_count = 0

            for card in cards:
                try:
                    if card.is_visible():
                        link_elem = card.locator('a[data-testid="result-title-a"]').first
                        if link_elem:
                            href = link_elem.get_attribute("href") or ""
                            if href.startswith('http'):
                                # Extrair domínio
                                domain = href.split('/')[2].lower() if '/' in href else ''

                                # ✅ Filtrar blacklist
                                if domain and not any(host in domain for host in blacklist_hosts):
                                    if href not in urls:
                                        urls.append(href)
                                else:
                                    filtered_count += 1
                except:
                    continue

            self.logger.log('success', f"{len(urls)} links coletados")
            if filtered_count > 0:
                self.logger.log('warning', f"{filtered_count} links filtrados (blacklist)")
            self.logger.dedent()
            return urls

        except Exception as e:
            self.logger.dedent()
            self.logger.log('error', f"Erro: {str(e)[:50]}")
            return []

    def extract_company_data(self, url: str, max_emails: int) -> CompanyModel:
        """
        NOVO SISTEMA DE EXTRAÇÃO (compatível)

        Args:
            url: URL
            max_emails: Máximo de emails

        Returns:
            CompanyModel
        """
        self.logger.log_step(f"Extraindo dados de: {url[:60]}...", 'target')

        try:
            # Usar ScraperCoordinator (novo sistema)
            self.logger.log('robot', "Executando sistema inteligente...")
            self.logger.indent()

            result = self.coordinator.scrape(url)

            self.logger.dedent()

            if result.success:
                company = self._convert_to_company_model(result.data, url)

                # Log resumo
                email_count = len(company.emails.split(',')) if company.emails else 0
                phone_count = len(company.phone.split(',')) if company.phone else 0

                self.logger.log('chart', f"Resultados: {email_count} email(s), {phone_count} telefone(s)")
                self.logger.log_step_end("Extração concluída", 'success')

                return company
            else:
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
            self.logger.log_step_end(f"Erro: {str(e)[:40]}", 'error')
            return CompanyModel(
                name="",
                emails="",
                domain=self._extract_domain(url),
                url=url,
                address="",
                phone="",
                html_content=""
            )
        finally:
            self.logger.reset_indent()

    def _convert_to_company_model(self, extraction_result, url: str) -> CompanyModel:
        """Converte para CompanyModel legado"""
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
