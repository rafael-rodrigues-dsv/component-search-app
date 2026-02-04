"""
DuckDuckGo Scraper V2 - Sistema Inteligente
"""
from typing import List
from src.domain.scrapers.orchestrator.scraper_coordinator import ScraperCoordinator
from src.domain.scrapers.utils.scraper_logger import ScraperLogger
from src.infrastructure.scrapers.switcher.yaml_config_loader import get_scraper_config
from src.domain.models.company_model import CompanyModel


class DuckDuckGoScraperV2:
    """
    DuckDuckGo Scraper V2 - Sistema Inteligente

    Interface compatível com scraper legado
    """

    def __init__(self, driver_manager):
        self.driver_manager = driver_manager
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

            self.logger.log('web', "Acessando duckduckgo.com...")
            self.logger.indent()

            # ✅ Respeitar delays do application.yaml
            from src.infrastructure.config.config_manager import ConfigManager
            cfg = ConfigManager()
            page_load_min = cfg.get_config_value('search.delays.duckduckgo.page_load_min', 0.03)
            page_load_max = cfg.get_config_value('search.delays.duckduckgo.page_load_max', 0.1)
            search_dwell_min = cfg.get_config_value('search.delays.duckduckgo.search_dwell_min', 0.03)
            search_dwell_max = cfg.get_config_value('search.delays.duckduckgo.search_dwell_max', 0.08)

            driver = self.driver_manager.get_driver()
            driver.get("https://duckduckgo.com")

            # ✅ Delay após carregar página
            delay = random.uniform(page_load_min, page_load_max)
            self.logger.log('clock', f"Aguardando {delay:.2f}s (page_load)...")
            time.sleep(delay)

            self.logger.log('success', "Página carregada")

            self.logger.log('keyboard', "Digitando termo de busca...")

            # Buscar campo de busca
            search_box = driver.find_element("name", "q")
            search_box.send_keys(search_term)

            # ✅ Delay após digitar
            delay = random.uniform(search_dwell_min, search_dwell_max)
            self.logger.log('clock', f"Aguardando {delay:.2f}s (search_dwell)...")
            time.sleep(delay)

            search_box.submit()

            self.logger.log('success', "Termo enviado")

            # ✅ Aguardar resultados carregarem
            time.sleep(2)

            self.logger.log('success', "Resultados carregados")
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
            driver = self.driver_manager.get_driver()

            # Extrair links
            links = driver.find_elements("css selector", "a[href]")
            urls = []
            filtered_count = 0

            for link in links:
                try:
                    href = link.get_attribute('href')
                    if href and href.startswith('http'):
                        # Extrair domínio
                        domain = href.split('/')[2].lower() if '/' in href else ''

                        # ✅ Filtrar blacklist (mesma lógica do scraper legado)
                        # Verifica se QUALQUER host da blacklist está no domínio (substring)
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
