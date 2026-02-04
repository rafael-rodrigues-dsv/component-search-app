"""
Google Scraper V2 - Sistema Inteligente
"""
from typing import List
from src.domain.scrapers.orchestrator.scraper_coordinator import ScraperCoordinator
from src.domain.scrapers.utils.scraper_logger import ScraperLogger
from src.infrastructure.scrapers.switcher.yaml_config_loader import get_scraper_config
from src.domain.models.company_model import CompanyModel


class GoogleScraperV2:
    """
    Google Scraper V2 - Sistema Inteligente

    Características:
    - Fast Path prioritário
    - Classificação automática
    - Budget controlado
    - Logging transparente
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

            self.logger.log('web', "Acessando google.com...")
            self.logger.indent()

            # ✅ Respeitar delays do application.yaml
            from src.infrastructure.config.config_manager import ConfigManager
            cfg = ConfigManager()
            page_load_min = cfg.get_config_value('search.delays.google.page_load_min', 0.05)
            page_load_max = cfg.get_config_value('search.delays.google.page_load_max', 0.15)
            search_dwell_min = cfg.get_config_value('search.delays.google.search_dwell_min', 0.05)
            search_dwell_max = cfg.get_config_value('search.delays.google.search_dwell_max', 0.1)

            self.page.goto("https://www.google.com", wait_until='domcontentloaded', timeout=30000)

            # ✅ Delay após carregar página (evitar detecção de bot)
            delay = random.uniform(page_load_min, page_load_max)
            self.logger.log('clock', f"Aguardando {delay:.2f}s (page_load)...")
            time.sleep(delay)

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
                    self.page.fill(selector, term, timeout=5000)

                    # ✅ Delay após digitar (simular digitação humana)
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

            # Aguardar resultados (aumentado para 30s para evitar captcha/timeouts)
            try:
                self.page.wait_for_selector('div.g, div.tF2Cxc, #search', timeout=30000)
                self.logger.log('success', "Resultados carregados")
                self.logger.dedent()
                return True
            except:
                self.logger.log('warning', "Timeout aguardando resultados (30s) - possível captcha")
                self.logger.dedent()
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
            # Extrair links dos resultados
            links = self.page.query_selector_all('a')
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
                            if href not in urls:  # Evitar duplicados
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
