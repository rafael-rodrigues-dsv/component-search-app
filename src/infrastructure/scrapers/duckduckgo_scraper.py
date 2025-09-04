"""
DuckDuckGo Scraper Rápido - Versão otimizada para velocidade
"""
import random
import re
import time
from typing import List

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException, TimeoutException

from src.infrastructure.config.delay_config import get_scraper_delays
from ..drivers.web_driver import WebDriverManager
from ...domain.services.email_domain_service import EmailValidationService
from ...domain.models.company_model import CompanyModel
from ..network.retry_manager import RetryManager


class DuckDuckGoScraper:
    """Scraper rápido para DuckDuckGo"""

    def __init__(self, driver_manager: WebDriverManager):
        self.driver_manager = driver_manager
        self.validation_service = EmailValidationService()
        self.delays = get_scraper_delays("DUCKDUCKGO")  # Delays específicos do DuckDuckGo

    @RetryManager.with_retry(max_attempts=3, base_delay=2.0, exceptions=(WebDriverException, TimeoutException))
    def search(self, query: str, max_retries: int = 2) -> bool:
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

    @RetryManager.with_retry(max_attempts=2, base_delay=1.0, exceptions=(WebDriverException, TimeoutException))
    def extract_company_data(self, url: str, max_emails: int) -> CompanyModel:
        """Extração rápida de dados da empresa"""
        try:
            self.driver_manager.driver.execute_script("window.open(arguments[0],'_blank');", url)
            self.driver_manager.driver.switch_to.window(self.driver_manager.driver.window_handles[-1])

            WebDriverWait(self.driver_manager.driver, 8).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            time.sleep(random.uniform(*self.delays["page_load"]))

            # Scroll rápido
            self.driver_manager.driver.execute_script("window.scrollBy(0, 2000);")
            time.sleep(random.uniform(*self.delays["scroll"]))

            # Capturar HTML content para geolocalização
            html_content = self.driver_manager.driver.page_source
            
            email_list = self._extract_emails_fast()[:max_emails]
            emails_string = self.validation_service.validate_and_join_emails(email_list)
            phone_list = self._extract_phones_fast()[:3]  # Máximo 3 telefones
            phones_string = self.validation_service.validate_and_join_phones(phone_list)
            name = self._get_company_name_fast(url)
            domain = self.validation_service.extract_domain_from_url(url)

            return CompanyModel(name=name, emails=emails_string, domain=domain, url=url, address="",
                                phone=phones_string, html_content=html_content)

        except Exception:
            return CompanyModel(name="", emails="", domain="", url=url, html_content="")
        finally:
            try:
                if len(self.driver_manager.driver.window_handles) > 1:
                    self.driver_manager.driver.close()
                    self.driver_manager.driver.switch_to.window(self.driver_manager.driver.window_handles[0])
            except Exception as e:
                print(f"[DEBUG] Erro ao fechar janela: {str(e)[:30]}")

    def _extract_emails_fast(self) -> List[str]:
        """Extração rápida de e-mails"""
        emails = set()

        try:
            # Busca no texto da página
            page_source = self.driver_manager.driver.page_source

            # Primeiro separa por delimitadores comuns
            text_parts = re.split(r'[;|,\s]+', page_source)

            for part in text_parts:
                # Busca e-mails em cada parte separadamente
                found_emails = re.findall(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}', part)

                for email in found_emails:
                    clean_email = email.strip().lower()
                    if self.validation_service.is_valid_email(clean_email):
                        emails.add(clean_email)
                        if len(emails) >= 5:  # Limite para velocidade
                            break

                if len(emails) >= 5:
                    break
        except Exception as e:
            print(f"[DEBUG] Erro na extração de e-mails: {str(e)[:30]}")

        return list(emails)

    def _extract_phones_fast(self) -> list:
        """Extração rápida de telefones"""
        phones = set()

        try:
            # Busca no texto da página
            page_source = self.driver_manager.driver.page_source

            # Padrões mais específicos de telefone brasileiro
            import re
            phone_patterns = [
                r'\([1-9][1-9]\)\s?9\d{4}[-\s]?\d{4}',  # (11) 99999-9999
                r'\([1-9][1-9]\)\s?[2-5]\d{3}[-\s]?\d{4}',  # (11) 3333-4444
                r'[1-9][1-9]\s9\d{4}[-\s]?\d{4}',  # 11 99999-9999
                r'[1-9][1-9]\s[2-5]\d{3}[-\s]?\d{4}',  # 11 3333-4444
            ]

            for pattern in phone_patterns:
                found_phones = re.findall(pattern, page_source)
                for phone in found_phones:
                    clean_phone = re.sub(r'[^0-9]', '', phone)
                    if self.validation_service.is_valid_phone(clean_phone):
                        phones.add(clean_phone)
                        if len(phones) >= 3:
                            break
                if len(phones) >= 3:
                    break
        except Exception as e:
            print(f"[DEBUG] Erro na extração de telefones: {str(e)[:30]}")

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