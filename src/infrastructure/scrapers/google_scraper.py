#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Scraper Rápido - Versão otimizada para velocidade
"""
import random
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config.settings import SCRAPER_DELAYS
from ...domain.email_service import EmailValidationService


class GoogleScraper:
    """Scraper rápido para busca no Google"""
    
    def __init__(self, driver):
        self.driver = driver
        self.base_url = "https://www.google.com"
        self.validation_service = EmailValidationService()
    
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
        from ...domain.models.company_model import CompanyModel
        
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
            
            # Primeiro separa por delimitadores comuns
            text_parts = re.split(r'[;|,\s]+', page_source)
            
            emails = []
            for part in text_parts:
                # Busca e-mails em cada parte separadamente
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                found_emails = re.findall(email_pattern, part)
                
                for email in found_emails:
                    clean_email = email.strip().lower()
                    if self.validation_service.is_valid_email(clean_email) and clean_email not in [e.lower() for e in emails]:
                        emails.append(clean_email)
                        if len(emails) >= max_emails:
                            break
                
                if len(emails) >= max_emails:
                    break
            
            # Valida e concatena e-mails (emails já é uma lista)
            emails_string = self.validation_service.validate_and_join_emails(emails)
            
            # Extração de telefones
            phones = self._extract_phones_fast(page_source)
            phones_string = self.validation_service.validate_and_join_phones(phones)
            
            # Nome da empresa (título da página)
            try:
                name = self.driver.title or url.split('/')[2]
                name = name.strip()[:50]  # Limita tamanho
            except:
                name = url.split('/')[2]
            
            return CompanyModel(
                name=name,
                emails=emails_string,
                domain=url.split('/')[2] if '/' in url else url,
                url=url,
                address="",
                phone=phones_string
            )
            
        except Exception as e:
            print(f"[ERRO] Falha ao extrair dados de {url}: {str(e)[:50]}")
            return CompanyModel(
                name="", 
                emails="", 
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
    
    def _extract_phones_fast(self, page_source) -> list:
        """Extração rápida de telefones"""
        phones = set()
        
        try:
            # Padrões mais específicos de telefone brasileiro
            import re
            phone_patterns = [
                r'\([1-9][1-9]\)\s?9\d{4}[-\s]?\d{4}',     # (11) 99999-9999
                r'\([1-9][1-9]\)\s?[2-5]\d{3}[-\s]?\d{4}', # (11) 3333-4444
                r'[1-9][1-9]\s9\d{4}[-\s]?\d{4}',          # 11 99999-9999
                r'[1-9][1-9]\s[2-5]\d{3}[-\s]?\d{4}',      # 11 3333-4444
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
        except:
            pass
        
        return list(phones)
    
