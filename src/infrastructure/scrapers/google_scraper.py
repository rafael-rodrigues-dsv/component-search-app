#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Scraper - Busca e extração de resultados no Google com anti-detecção
"""
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from config.settings import SEARCH_DWELL, SCROLL_STEPS, SCROLL_PAUSE


class GoogleScraper:
    """Scraper para busca no Google"""
    
    def __init__(self, driver):
        self.driver = driver
        self.base_url = "https://www.google.com"
    
    def search(self, term, max_results=50):
        """Executa busca no Google e retorna URLs dos resultados"""
        try:
            # Simulação humana: navegação gradual
            self._human_navigation_to_google()
            
            # Aceitar cookies com simulação humana
            self._handle_cookies_humanly()
            
            # Busca com simulação de digitação humana
            if not self._perform_human_search(term):
                return []
            
            # Verifica se foi bloqueado
            if self._check_captcha_or_block():
                print("[AVISO] Google detectou bot - tentando contornar...")
                return self._handle_detection(term)
            
            # Coletar URLs com comportamento humano
            return self._collect_results_humanly(max_results)
            
        except Exception as e:
            print(f"[ERRO] Falha na busca Google: {e}")
            return []
    
    def _scroll_page(self):
        """Faz scroll na página para simular comportamento humano"""
        # Método mantido para compatibilidade
        self._human_scroll()
    
    def _is_valid_url(self, url):
        """Verifica se URL é válida para processamento"""
        if not url or not url.startswith("http"):
            return False
        
        # Filtrar URLs do próprio Google
        invalid_patterns = [
            "google.com", "youtube.com", "maps.google", "translate.google",
            "accounts.google", "support.google", "policies.google"
        ]
        
        return not any(pattern in url.lower() for pattern in invalid_patterns)
    
    def _human_navigation_to_google(self):
        """Navegação humana para Google usando busca direta"""
        # Vai direto para página de busca (evita detecção na home)
        search_url = "https://www.google.com/search?q=test"
        self.driver.get(search_url)
        
        # Simula leitura da página
        time.sleep(random.uniform(3.0, 6.0))
        
        # Movimento de mouse mais natural
        try:
            actions = ActionChains(self.driver)
            # Simula movimento de leitura
            for _ in range(3):
                x = random.randint(200, 800)
                y = random.randint(200, 600)
                actions.move_by_offset(x, y)
                actions.pause(random.uniform(0.5, 1.2))
            actions.perform()
        except:
            pass
    
    def _handle_cookies_humanly(self):
        """Lida com cookies de forma humana"""
        try:
            # Espera um pouco antes de aceitar
            time.sleep(random.uniform(1.0, 2.5))
            
            # Tenta vários seletores de aceitar cookies
            selectors = [
                "//button[contains(text(), 'Aceitar')]",
                "//button[contains(text(), 'Accept')]",
                "//button[contains(text(), 'Aceito')]",
                "//div[@id='L2AGLb']//button",
                "button[id='L2AGLb']"
            ]
            
            for selector in selectors:
                try:
                    if selector.startswith('//'):
                        btn = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                    else:
                        btn = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                    
                    # Movimento humano para o botão
                    actions = ActionChains(self.driver)
                    actions.move_to_element(btn)
                    actions.pause(random.uniform(0.3, 0.8))
                    actions.click()
                    actions.perform()
                    
                    time.sleep(random.uniform(0.5, 1.2))
                    break
                except:
                    continue
        except:
            pass
    
    def _perform_human_search(self, term):
        """Executa busca simulando comportamento humano"""
        try:
            # Usa URL direta para evitar detecção
            import urllib.parse
            encoded_term = urllib.parse.quote_plus(term)
            search_url = f"https://www.google.com/search?q={encoded_term}&hl=pt-BR&gl=BR"
            
            # Navegação gradual
            self.driver.get(search_url)
            
            # Simula tempo de carregamento
            time.sleep(random.uniform(4.0, 8.0))
            
            # Verifica se carregou
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.g, div.tF2Cxc"))
                )
                return True
            except:
                # Se não encontrou resultados, tenta método tradicional
                return self._fallback_search(term)
            
        except Exception as e:
            print(f"[ERRO] Falha na busca direta: {e}")
            return self._fallback_search(term)
    
    def _fallback_search(self, term):
        """Método de busca alternativo"""
        try:
            # Vai para Google simples
            self.driver.get("https://www.google.com/ncr")
            time.sleep(random.uniform(2.0, 4.0))
            
            # Encontra campo de busca
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            
            # Digitação rápida
            search_box.clear()
            search_box.send_keys(term)
            time.sleep(random.uniform(1.0, 2.0))
            search_box.submit()
            
            time.sleep(random.uniform(3.0, 5.0))
            return True
            
        except:
            return False
    
    def _check_captcha_or_block(self):
        """Verifica se foi bloqueado ou tem captcha"""
        page_source = self.driver.page_source.lower()
        
        block_indicators = [
            "captcha", "robot", "automated", "unusual traffic",
            "verify you're human", "prove you're not a robot",
            "suspicious activity", "blocked"
        ]
        
        return any(indicator in page_source for indicator in block_indicators)
    
    def _handle_detection(self, term):
        """Lida com detecção de bot usando estratégias alternativas"""
        try:
            print("[INFO] Tentando contornar detecção...")
            
            # Estratégia 1: Usar DuckDuckGo como fallback
            try:
                ddg_url = f"https://duckduckgo.com/?q={term.replace(' ', '+')}"
                self.driver.get(ddg_url)
                time.sleep(random.uniform(3, 5))
                
                # Extrai links do DuckDuckGo
                links = self.driver.find_elements(By.CSS_SELECTOR, "a[data-testid='result-title-a']")
                urls = []
                for link in links[:20]:
                    try:
                        url = link.get_attribute("href")
                        if url and self._is_valid_url(url):
                            urls.append(url)
                    except:
                        continue
                
                if urls:
                    print("[OK] Usando DuckDuckGo como alternativa")
                    return urls
            except:
                pass
            
            # Estratégia 2: Esperar e tentar Google novamente
            print("[INFO] Aguardando para nova tentativa...")
            time.sleep(random.uniform(30, 60))
            
            # Limpa cookies e tenta novamente
            self.driver.delete_all_cookies()
            time.sleep(2)
            
            return self._perform_human_search(term) and self._collect_results_humanly(20) or []
            
        except:
            return []
    
    def _collect_results_humanly(self, max_results):
        """Coleta resultados com comportamento humano"""
        urls = []
        
        # Scroll humano primeiro
        self._human_scroll()
        
        # Extrai links com múltiplos seletores
        result_selectors = [
            "div.g a[href]:not([href*='google.com'])",
            "div.tF2Cxc a[href]:not([href*='google.com'])", 
            "div.yuRUbf a[href]:not([href*='google.com'])",
            "h3 a[href]:not([href*='google.com'])",
            "a[data-ved][href]:not([href*='google.com'])"
        ]
        
        for selector in result_selectors:
            try:
                links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for link in links:
                    try:
                        url = link.get_attribute("href")
                        if url and self._is_valid_url(url) and url not in urls:
                            urls.append(url)
                            if len(urls) >= max_results:
                                return urls[:max_results]
                    except:
                        continue
                        
                if urls:  # Se encontrou resultados, para
                    break
            except:
                continue
        
        # Se poucos resultados, tenta próxima página
        if len(urls) < 10:
            try:
                next_url = f"{self.driver.current_url}&start=10"
                self.driver.get(next_url)
                time.sleep(random.uniform(3, 5))
                
                # Extrai mais resultados
                for selector in result_selectors:
                    try:
                        links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for link in links:
                            try:
                                url = link.get_attribute("href")
                                if url and self._is_valid_url(url) and url not in urls:
                                    urls.append(url)
                                    if len(urls) >= max_results:
                                        return urls[:max_results]
                            except:
                                continue
                    except:
                        continue
            except:
                pass
        
        return urls[:max_results]
    
    def _human_scroll(self):
        """Scroll com comportamento humano"""
        # Scroll gradual
        for _ in range(random.randint(3, 6)):
            scroll_amount = random.randint(200, 500)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            time.sleep(random.uniform(0.5, 1.2))
        
        # Volta um pouco (comportamento humano)
        self.driver.execute_script("window.scrollBy(0, -100);")
        time.sleep(random.uniform(0.3, 0.8))
    
    def _go_to_next_page_humanly(self):
        """Vai para próxima página humanamente"""
        try:
            # Scroll para baixo primeiro
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(1.0, 2.0))
            
            # Procura botão de próxima página
            next_selectors = [
                "a#pnnext", "a[aria-label='Next']", 
                "a[aria-label='Próxima']", "span:contains('Next')"
            ]
            
            for selector in next_selectors:
                try:
                    next_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_btn.is_enabled():
                        # Movimento humano
                        actions = ActionChains(self.driver)
                        actions.move_to_element(next_btn)
                        actions.pause(random.uniform(0.5, 1.0))
                        actions.click()
                        actions.perform()
                        return True
                except:
                    continue
            
            return False
        except:
            return False