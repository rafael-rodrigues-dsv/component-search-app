"""
Camada de Infraestrutura - Scraper DuckDuckGo
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


class DuckDuckGoScraper:
    """Scraper para DuckDuckGo"""
    
    def __init__(self, driver_manager: WebDriverManager):
        self.driver_manager = driver_manager
        self.validation_service = EmailValidationService()
    
    def search(self, query: str) -> bool:
        """Executa busca no DuckDuckGo"""
        try:
            self.driver_manager.driver.get("https://duckduckgo.com/")
            WebDriverWait(self.driver_manager.driver, 20).until(
                EC.presence_of_element_located((By.ID, "searchbox_input"))
            )
            
            search_box = self.driver_manager.driver.find_element(By.ID, "searchbox_input")
            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.ENTER)
            
            WebDriverWait(self.driver_manager.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='result']"))
            )
            time.sleep(random.uniform(0.8, 1.6))
            return True
            
        except TimeoutException:
            return False
    
    def get_result_links(self, blacklist_hosts: List[str]) -> List[str]:
        """Extrai links dos resultados"""
        links = []
        try:
            cards = self.driver_manager.driver.find_elements(By.CSS_SELECTOR, "[data-testid='result']")
            for card in cards:
                link_elements = card.find_elements(By.CSS_SELECTOR, "a[data-testid='result-title-a']")
                if not link_elements:
                    link_elements = card.find_elements(By.CSS_SELECTOR, "a.result__a")
                
                if link_elements:
                    href = link_elements[0].get_attribute("href") or ""
                    if href.startswith("http") and not self._is_blacklisted(href, blacklist_hosts):
                        links.append(href)
        except Exception:
            pass
        
        return self._deduplicate_links(links)
    
    def extract_company_data(self, url: str, max_emails: int) -> Company:
        """Extrai dados da empresa do site"""
        try:
            self.driver_manager.driver.execute_script("window.open(arguments[0],'_blank');", url)
            self.driver_manager.driver.switch_to.window(self.driver_manager.driver.window_handles[-1])
            
            WebDriverWait(self.driver_manager.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            time.sleep(random.uniform(1.0, 2.0))
            self._human_scroll()
            time.sleep(random.uniform(6, 12))
            
            emails = self._extract_emails()[:max_emails]
            name = self._get_company_name(url)
            domain = self.validation_service.extract_domain_from_url(url)
            address = self._extract_address()
            
            return Company(name=name, emails=emails, domain=domain, url=url, address=address)
            
        except Exception:
            return Company(name="", emails=[], domain="", url=url)
        finally:
            try:
                if len(self.driver_manager.driver.window_handles) > 1:
                    self.driver_manager.driver.close()
                    self.driver_manager.driver.switch_to.window(self.driver_manager.driver.window_handles[0])
            except:
                pass
    
    def _human_scroll(self):
        """Simula rolagem humana"""
        try:
            height = self.driver_manager.driver.execute_script("return document.body.scrollHeight") or 2000
        except:
            height = 2000
        
        steps = random.randint(6, 10)
        for i in range(1, steps + 1):
            y = int(height * i / steps)
            self.driver_manager.driver.execute_script(f"window.scrollTo(0, {y});")
            time.sleep(random.uniform(0.8, 2.0))
    
    def _extract_emails(self) -> List[str]:
        """Extrai e-mails da página"""
        emails = set()
        
        try:
            text = self.driver_manager.driver.find_element(By.TAG_NAME, "body").text
            found_emails = re.findall(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", text)
            for email in found_emails:
                if self.validation_service.is_valid_email(email):
                    emails.add(email.lower())
        except:
            pass
        
        try:
            mailto_links = self.driver_manager.driver.find_elements(By.CSS_SELECTOR, "a[href^='mailto:']")
            for link in mailto_links:
                href = link.get_attribute("href") or ""
                email = href.replace("mailto:", "").split("?")[0]
                if email and self.validation_service.is_valid_email(email):
                    emails.add(email.lower())
        except:
            pass
        
        return list(emails)
    
    def _get_company_name(self, url: str) -> str:
        """Extrai nome da empresa"""
        try:
            for tag in ["header", "h1", "h2"]:
                elements = self.driver_manager.driver.find_elements(By.TAG_NAME, tag)
                for element in elements:
                    text = element.text.strip()
                    if 3 <= len(text) <= 80:
                        return text
            
            title = self.driver_manager.driver.title or ""
            if title.strip():
                return title.strip()[:80]
                
        except:
            pass
        
        return self.validation_service.extract_domain_from_url(url)
    
    def _extract_address(self) -> str:
        """Extrai endereço da empresa"""
        try:
            # Busca por padrões de endereço
            body_text = self.driver_manager.driver.find_element(By.TAG_NAME, "body").text
            
            # Padrões de endereço brasileiro
            import re
            address_patterns = [
                r'[A-ZÀ-ſ][a-zÀ-ſ\s]+,\s*\d+[\w\s,-]*\d{5}-?\d{3}',  # Rua, número, CEP
                r'Rua\s+[A-ZÀ-ſ][\w\s,.-]+\d+[\w\s,-]*',  # Rua + nome + número
                r'Av[\w\s.]*[A-ZÀ-ſ][\w\s,.-]+\d+[\w\s,-]*',  # Avenida
                r'[A-ZÀ-ſ][\w\s,.-]+\d{5}-?\d{3}[\w\s,-]*São Paulo'  # Com CEP e SP
            ]
            
            for pattern in address_patterns:
                matches = re.findall(pattern, body_text)
                if matches:
                    return matches[0][:100]  # Limita a 100 caracteres
            
            # Busca por elementos com classes relacionadas a endereço
            address_selectors = [
                '[class*="address"]', '[class*="endereco"]', '[class*="location"]',
                '[class*="contact"]', '[id*="address"]', '[id*="endereco"]'
            ]
            
            for selector in address_selectors:
                elements = self.driver_manager.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    if 10 <= len(text) <= 150 and any(word in text.lower() for word in ['rua', 'av', 'avenida', 'cep']):
                        return text[:100]
                        
        except:
            pass
        
        return ""
    
    def _is_blacklisted(self, url: str, blacklist: List[str]) -> bool:
        """Verifica se URL está na blacklist"""
        url_lower = url.lower()
        return any(blocked in url_lower for blocked in blacklist)
    
    def _deduplicate_links(self, links: List[str]) -> List[str]:
        """Remove links duplicados mantendo ordem"""
        seen = set()
        unique = []
        for link in links:
            if link not in seen:
                unique.append(link)
                seen.add(link)
        return unique