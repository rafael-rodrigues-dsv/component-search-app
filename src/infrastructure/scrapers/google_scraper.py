#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Scraper Rápido - Versão otimizada para velocidade
"""
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from config.settings import SCRAPER_DELAYS


class GoogleScraper:
    """Scraper rápido para busca no Google"""
    
    def __init__(self, driver):
        self.driver = driver
        self.base_url = "https://www.google.com"
    
    def search(self, term, max_results=50):
        """Executa busca no Google de forma rápida"""
        try:
            # Busca direta sem delays longos
            import urllib.parse
            encoded_term = urllib.parse.quote_plus(term)
            search_url = f"https://www.google.com/search?q={encoded_term}&hl=pt-BR&gl=BR"
            
            self.driver.get(search_url)
            time.sleep(random.uniform(*SCRAPER_DELAYS["page_load"]))
            
            # Verifica se carregou
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.g, div.tF2Cxc"))
                )
                return True  # Sucesso na busca
            except:
                return self._fallback_search_simple(term)
            
        except Exception as e:
            print(f"[ERRO] Falha na busca Google: {e}")
            return False
    
    def _fallback_search_simple(self, term):
        """Fallback simples que retorna True/False"""
        try:
            ddg_url = f"https://duckduckgo.com/?q={term.replace(' ', '+')}"
            self.driver.get(ddg_url)
            time.sleep(random.uniform(*SCRAPER_DELAYS["page_load"]))
            return True
        except:
            return False
    
    def get_result_links(self, blacklist_hosts):
        """Retorna links dos resultados da página atual"""
        urls = []
        
        # Scroll para carregar mais resultados
        self.driver.execute_script("window.scrollBy(0, 1500);")
        time.sleep(random.uniform(*SCRAPER_DELAYS["scroll"]))
        
        selectors = [
            "div.g a[href]:not([href*='google.com'])",
            "div.tF2Cxc a[href]:not([href*='google.com'])", 
            "h3 a[href]:not([href*='google.com'])"
        ]
        
        for selector in selectors:
            try:
                links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for link in links:
                    try:
                        url = link.get_attribute("href")
                        if url and self._is_valid_url(url):
                            # Verifica blacklist
                            domain = url.split('/')[2].lower()
                            if not any(host in domain for host in blacklist_hosts):
                                urls.append(url)
                    except:
                        continue
                if urls:
                    break
            except:
                continue
        
        return urls
    
    def go_to_next_page(self):
        """Navega para a próxima página de resultados"""
        try:
            # Método 1: Usar parâmetro start na URL
            current_url = self.driver.current_url
            
            if "&start=" in current_url:
                # Incrementa o start existente
                import re
                start_match = re.search(r'&start=(\d+)', current_url)
                if start_match:
                    current_start = int(start_match.group(1))
                    new_start = current_start + 10
                    new_url = re.sub(r'&start=\d+', f'&start={new_start}', current_url)
                else:
                    new_url = current_url + "&start=10"
            else:
                # Adiciona start=10 para segunda página
                new_url = current_url + "&start=10"
            
            self.driver.get(new_url)
            time.sleep(random.uniform(*SCRAPER_DELAYS["page_load"]))
            
            # Verifica se carregou resultados
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.g, div.tF2Cxc"))
                )
                return True
            except:
                return False
                
        except Exception as e:
            print(f"    [AVISO] Falha ao ir para próxima página: {str(e)[:30]}")
            return False
    
    def extract_company_data(self, url, max_emails):
        """Extrai dados da empresa do site usando sistema de abas"""
        from ...domain.email_processor import Company
        
        try:
            # Abre site em nova aba (igual ao DuckDuckGo)
            self.driver.execute_script("window.open(arguments[0],'_blank');", url)
            self.driver.switch_to.window(self.driver.window_handles[-1])
            
            # Aguarda carregamento
            WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            time.sleep(random.uniform(*SCRAPER_DELAYS["page_load"]))
            
            # Scroll rápido para carregar conteúdo
            self.driver.execute_script("window.scrollBy(0, 2000);")
            time.sleep(random.uniform(*SCRAPER_DELAYS["scroll"]))
            
            # Extração rápida de e-mails
            page_source = self.driver.page_source
            
            import re
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            found_emails = re.findall(email_pattern, page_source)
            
            # Valida e limita e-mails
            emails = []
            for email in found_emails:
                if self._is_valid_email(email) and email.lower() not in [e.lower() for e in emails]:
                    emails.append(email.lower())
                    if len(emails) >= max_emails:
                        break
            
            # Nome da empresa (título da página)
            try:
                name = self.driver.title or url.split('/')[2]
                name = name.strip()[:50]  # Limita tamanho
            except:
                name = url.split('/')[2]
            
            return Company(
                name=name,
                emails=emails,
                domain=url.split('/')[2] if '/' in url else url,
                url=url,
                address="",
                phone=""
            )
            
        except Exception as e:
            print(f"[ERRO] Falha ao extrair dados de {url}: {str(e)[:50]}")
            return Company(
                name="", 
                emails=[], 
                domain=url.split('/')[2] if '/' in url else url,
                url=url,
                address="", 
                phone=""
            )
        finally:
            # Fecha aba atual e volta para aba de resultados (igual ao DuckDuckGo)
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
    
    def _is_valid_url(self, url):
        """Verifica se URL é válida"""
        if not url or not url.startswith("http"):
            return False
        
        invalid_patterns = [
            "google.com", "youtube.com", "maps.google", "translate.google"
        ]
        
        return not any(pattern in url.lower() for pattern in invalid_patterns)
    
    def _is_valid_email(self, email):
        """Valida formato do e-mail"""
        import re
        email = email.strip().lower()
        if not re.match(r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$", email):
            return False
        bad_bits = ["example", "exemplo", "teste", "email@", "@email", "no-reply", "noreply", "spam"]
        return not any(b in email for b in bad_bits)