"""
DuckDuckGo Scraper Rápido - Versão otimizada para velocidade
"""
import random
import re
import time
from typing import List

from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.infrastructure.config.delay_config import get_scraper_delays
from src.infrastructure.config.config_manager import ConfigManager
from ..drivers.web_driver import WebDriverManager
from ..network.retry_manager import RetryManager
from ...domain.models.company_model import CompanyModel
from ...domain.services.email_domain_service import EmailValidationService


class DuckDuckGoScraper:
    """Scraper rápido para DuckDuckGo"""

    def __init__(self, driver_manager: WebDriverManager):
        self.driver_manager = driver_manager
        self.validation_service = EmailValidationService()
        self.delays = get_scraper_delays("DUCKDUCKGO")  # Delays específicos do DuckDuckGo
        self.config = ConfigManager()  # Para acessar configurações de retry

    def search(self, query: str, max_retries: int = 2) -> bool:
        @RetryManager.with_retry(
            max_attempts=self.config.retry_max_attempts,
            base_delay=self.config.retry_base_delay,
            backoff_factor=self.config.retry_backoff_factor,
            max_delay=self.config.retry_max_delay,
            exceptions=(WebDriverException, TimeoutException)
        )
        def _search_impl():
            return self._search_implementation(query, max_retries)
        return _search_impl()
    
    def _search_implementation(self, query: str, max_retries: int = 2) -> bool:
        """Executa busca rápida no DuckDuckGo"""
        try:
            self.driver_manager.driver.get("https://duckduckgo.com/")

            search_box = WebDriverWait(self.driver_manager.driver, 10).until(
                EC.presence_of_element_located((By.ID, "searchbox_input"))
            )

            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.ENTER)

            WebDriverWait(self.driver_manager.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='result']"))
            )

            time.sleep(random.uniform(*self.delays["page_load"]))
            return True

        except Exception as e:
            print(f"    [ERRO] Busca falhou: {str(e)[:50]}")
            return False

    def get_result_links(self, blacklist_hosts: List[str]) -> List[str]:
        """Extrai links rapidamente"""
        links = []
        try:
            # Scroll para carregar mais resultados
            self.driver_manager.driver.execute_script("window.scrollBy(0, 1500);")
            time.sleep(random.uniform(*self.delays["scroll"]))

            cards = self.driver_manager.driver.find_elements(By.CSS_SELECTOR, "[data-testid='result']")
            for card in cards:
                link_elements = card.find_elements(By.CSS_SELECTOR, "a[data-testid='result-title-a']")

                if link_elements:
                    href = link_elements[0].get_attribute("href") or ""
                    if href.startswith("http") and not self._is_blacklisted(href, blacklist_hosts):
                        links.append(href)
        except Exception as e:
            print(f"    [DEBUG] Erro ao extrair links: {str(e)[:50]}")

        return list(set(links))  # Remove duplicatas

    def go_to_next_page(self):
        """Navega para a próxima página de resultados"""
        try:
            # Scroll para o final da página
            self.driver_manager.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(*self.delays["scroll"]))

            # Procura botão "More results" ou similar
            more_selectors = [
                "button[id='more-results']",
                "a[class*='more']",
                "button:contains('More')",
                "[data-testid='more-results']"
            ]

            for selector in more_selectors:
                try:
                    more_btn = self.driver_manager.driver.find_element(By.CSS_SELECTOR, selector)
                    if more_btn.is_displayed():
                        more_btn.click()
                        time.sleep(random.uniform(*self.delays["page_load"]))
                        return True
                except Exception as e:
                    print(f"    [DEBUG] Erro no seletor {selector}: {str(e)[:30]}")
                    continue

            # Se não encontrou botão, tenta scroll adicional para carregar mais
            for _ in range(3):
                self.driver_manager.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(random.uniform(*self.delays["scroll"]))

            return True  # Assume que carregou mais resultados

        except Exception:
            return False

    def extract_company_data(self, url: str, max_emails: int) -> CompanyModel:
        """Extração otimizada de dados da empresa usando sistema de abas"""
        try:
            print(f"    [INFO] Carregando site: {url}")
            
            # Abre site em nova aba (mantém aba de pesquisa aberta)
            self.driver_manager.driver.execute_script("window.open(arguments[0],'_blank');", url)
            self.driver_manager.driver.switch_to.window(self.driver_manager.driver.window_handles[-1])
            
            # Timeout muito agressivo - 5 segundos máximo
            self.driver_manager.driver.set_page_load_timeout(5)
            
            try:
                # Aguarda carregamento na nova aba
                WebDriverWait(self.driver_manager.driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                print(f"    [AVISO] Timeout no carregamento - continuando...")
                pass
            
            # Aguarda mínimo para HTML carregar
            try:
                WebDriverWait(self.driver_manager.driver, 2).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                print(f"    [AVISO] Body não carregou - tentando extrair mesmo assim")
                pass

            # Para carregamento forçadamente
            try:
                self.driver_manager.driver.execute_script("window.stop();")
            except:
                pass

            time.sleep(1)  # Delay fixo mínimo

            print(f"    [DEBUG] Fazendo scroll...")
            # Scroll mínimo
            self.driver_manager.driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(1)

            print(f"    [DEBUG] Capturando HTML...")
            # Capturar HTML (limitado para performance)
            html_content = self.driver_manager.driver.page_source
            if len(html_content) > 100000:  # Limita a 100KB
                html_content = html_content[:100000]
            print(f"    [DEBUG] HTML capturado: {len(html_content)} chars")

            print(f"    [DEBUG] Extraindo endereço...")
            # Extrair endereço formatado
            try:
                from src.infrastructure.utils.address_extractor import AddressExtractor
                endereco_formatado = AddressExtractor.extract_from_html(html_content)
                print(f"    [DEBUG] Endereço: {endereco_formatado.to_full_address()[:50] if endereco_formatado else 'Não encontrado'}")
                
            except Exception as e:
                print(f"    [DEBUG] Erro na extração de endereço: {str(e)[:30]}")
                endereco_formatado = None

            print(f"    [DEBUG] Extraindo emails...")
            # Extrações otimizadas
            email_list = self._extract_emails_fast(html_content)[:max_emails]
            emails_string = self.validation_service.validate_and_join_emails(email_list)
            print(f"    [DEBUG] Emails: {len(email_list)} encontrados")
            
            print(f"    [DEBUG] Extraindo telefones...")
            phone_list = self._extract_phones_fast(html_content)[:2]
            phones_string = self.validation_service.validate_and_join_phones(phone_list)
            print(f"    [DEBUG] Telefones: {len(phone_list)} encontrados")
            
            print(f"    [DEBUG] Extraindo nome da empresa...")
            name = self._get_company_name_fast(url)
            domain = self.validation_service.extract_domain_from_url(url)
            print(f"    [DEBUG] Nome: {name[:30]}... | Domain: {domain}")

            return CompanyModel(
                name=name,
                emails=emails_string,
                domain=domain,
                url=url,
                address=endereco_formatado or "",
                phone=phones_string,
                html_content=html_content
            )

        except Exception as e:
            print(f"    [ERRO] {str(e)[:50]}...")
            return CompanyModel(name="", emails="", domain="", url=url, html_content="")
        finally:
            # Fecha aba atual e volta para aba de pesquisa
            try:
                if len(self.driver_manager.driver.window_handles) > 1:
                    self.driver_manager.driver.close()
                    self.driver_manager.driver.switch_to.window(self.driver_manager.driver.window_handles[0])
                    print(f"    [INFO] Voltou para aba de pesquisa")
            except Exception as e:
                print(f"[DEBUG] Erro ao fechar aba: {str(e)[:30]}")

    def _extract_emails_fast(self, html_content: str) -> List[str]:
        """Extração ultra-rápida de e-mails"""
        emails = set()

        try:
            # Regex otimizada
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            found_emails = re.findall(email_pattern, html_content)

            for email in found_emails:
                email_lower = email.lower()
                if (len(email_lower) > 5 and
                        '.' in email_lower.split('@')[1] and
                        not any(bad in email_lower for bad in ['sentry.io', 'example.com'])):
                    emails.add(email_lower)
                    if len(emails) >= 3:
                        break

        except Exception:
            pass

        return list(emails)

    def _extract_phones_fast(self, html_content: str) -> list:
        """Extração ultra-rápida de telefones"""
        phones = set()

        try:
            # Padrão otimizado para telefones brasileiros
            phone_pattern = r'(?:\([1-9][1-9]\)\s?|[1-9][1-9]\s)[9][0-9]{4}[-\s]?[0-9]{4}|(?:\([1-9][1-9]\)\s?|[1-9][1-9]\s)[2-5][0-9]{3}[-\s]?[0-9]{4}'
            found_phones = re.findall(phone_pattern, html_content)

            for phone in found_phones:
                clean_phone = re.sub(r'[^\d]', '', phone)
                if len(clean_phone) in [10, 11] and clean_phone[:2] in ['11', '12', '13', '14', '15', '16', '17', '18',
                                                                        '19', '21']:
                    phones.add(phone)
                    if len(phones) >= 2:
                        break

        except Exception:
            pass

        return list(phones)

    def _get_company_name_fast(self, url: str) -> str:
        """Extração rápida do nome da empresa"""
        try:
            title = self.driver_manager.driver.title or ""
            if title.strip():
                return title.strip()[:50]
        except Exception as e:
            print(f"[DEBUG] Erro ao obter nome da empresa: {str(e)[:30]}")

        return self.validation_service.extract_domain_from_url(url)

    def _is_blacklisted(self, url: str, blacklist_hosts: List[str]) -> bool:
        """Verifica se URL está na blacklist"""
        url_lower = url.lower()
        return any(host in url_lower for host in blacklist_hosts)
