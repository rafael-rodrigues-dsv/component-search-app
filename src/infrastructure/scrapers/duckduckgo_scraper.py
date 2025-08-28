"""
DuckDuckGo Scraper Rápido - Versão otimizada para velocidade
"""
import time
import random
import re
from typing import List
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from ...domain.email_processor import Company, EmailValidationService
from ..web_driver import WebDriverManager
from config.settings import SCRAPER_DELAYS


class DuckDuckGoScraper:
    """Scraper rápido para DuckDuckGo"""
    
    def __init__(self, driver_manager: WebDriverManager):
        self.driver_manager = driver_manager
        self.validation_service = EmailValidationService()
    
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
            
            time.sleep(random.uniform(*SCRAPER_DELAYS["page_load"]))
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
            time.sleep(random.uniform(*SCRAPER_DELAYS["scroll"]))
            
            cards = self.driver_manager.driver.find_elements(By.CSS_SELECTOR, "[data-testid='result']")
            for card in cards:
                link_elements = card.find_elements(By.CSS_SELECTOR, "a[data-testid='result-title-a']")
                
                if link_elements:
                    href = link_elements[0].get_attribute("href") or ""
                    if href.startswith("http") and not self._is_blacklisted(href, blacklist_hosts):
                        links.append(href)
        except:
            pass
        
        return list(set(links))  # Remove duplicatas
    
    def go_to_next_page(self):
        """Navega para a próxima página de resultados"""
        try:
            # Scroll para o final da página
            self.driver_manager.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(*SCRAPER_DELAYS["scroll"]))
            
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
                        time.sleep(random.uniform(*SCRAPER_DELAYS["page_load"]))
                        return True
                except:
                    continue
            
            # Se não encontrou botão, tenta scroll adicional para carregar mais
            for _ in range(3):
                self.driver_manager.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(random.uniform(*SCRAPER_DELAYS["scroll"]))
            
            return True  # Assume que carregou mais resultados
            
        except Exception:
            return False
    
    def extract_company_data(self, url: str, max_emails: int) -> Company:
        """Extração rápida de dados da empresa"""
        try:
            self.driver_manager.driver.execute_script("window.open(arguments[0],'_blank');", url)
            self.driver_manager.driver.switch_to.window(self.driver_manager.driver.window_handles[-1])
            
            WebDriverWait(self.driver_manager.driver, 8).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            time.sleep(random.uniform(*SCRAPER_DELAYS["page_load"]))
            
            # Scroll rápido
            self.driver_manager.driver.execute_script("window.scrollBy(0, 2000);")
            time.sleep(random.uniform(*SCRAPER_DELAYS["scroll"]))
            
            emails = self._extract_emails_fast()[:max_emails]
            name = self._get_company_name_fast(url)
            domain = self.validation_service.extract_domain_from_url(url)
            
            return Company(name=name, emails=emails, domain=domain, url=url, address="", phone="")
            
        except Exception:
            return Company(name="", emails=[], domain="", url=url)
        finally:
            try:
                if len(self.driver_manager.driver.window_handles) > 1:
                    self.driver_manager.driver.close()
                    self.driver_manager.driver.switch_to.window(self.driver_manager.driver.window_handles[0])
            except:
                pass
    
    def _extract_emails_fast(self) -> List[str]:
        """Extração rápida de e-mails"""
        emails = set()
        
        try:
            # Busca no texto da página
            page_source = self.driver_manager.driver.page_source
            found_emails = re.findall(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}', page_source)
            
            for email in found_emails:
                if self.validation_service.is_valid_email(email):
                    emails.add(email.lower())
                    if len(emails) >= 5:  # Limite para velocidade
                        break
        except:
            pass
        
        return list(emails)
    
    def _get_company_name_fast(self, url: str) -> str:
        """Extração rápida do nome da empresa"""
        try:
            title = self.driver_manager.driver.title or ""
            if title.strip():
                return title.strip()[:50]
        except:
            pass
        
        return self.validation_service.extract_domain_from_url(url)
    
    def _is_blacklisted(self, url: str, blacklist_hosts: List[str]) -> bool:
        """Verifica se URL está na blacklist"""
        url_lower = url.lower()
        return any(host in url_lower for host in blacklist_hosts)