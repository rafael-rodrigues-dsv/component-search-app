#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Scraper Rápido - Versão otimizada para velocidade
"""
import random
import time

from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config.settings import MAX_PHONES_PER_SITE
from src.infrastructure.config.delay_config import get_scraper_delays
from ..network.human_behavior import HumanBehaviorSimulator
from ..network.retry_manager import RetryManager
from ...domain.services.email_domain_service import EmailValidationService

# Constantes para scraping
MAX_SCROLL_PIXELS = 1500
SECOND_PAGE_START = 10
MAX_TITLE_LENGTH = 50
MAX_ERROR_MESSAGE_LENGTH = 50
MAX_ERROR_URL_LENGTH = 30
PAGE_LOAD_TIMEOUT = 8
SEARCH_TIMEOUT = 5


class GoogleScraper:
    """Scraper rápido para busca no Google"""

    def __init__(self, driver):
        self.driver = driver
        self.base_url = "https://www.google.com"
        self.validation_service = EmailValidationService()
        self.human_behavior = HumanBehaviorSimulator()
        self.searches_count = 0
        self.delays = get_scraper_delays("GOOGLE")  # Delays específicos do Google

    @RetryManager.with_retry(max_attempts=3, base_delay=2.0, exceptions=(WebDriverException, TimeoutException))
    def search(self, term, max_results=50):
        """Executa busca no Google simulando comportamento humano"""
        try:
            # === NAVEGAÇÃO HUMANA ===
            # 1. Primeiro vai para Google.com (como humano faria)
            self.driver.get("https://www.google.com")
            time.sleep(random.uniform(2.0, 4.0))

            # 2. Simula movimento de mouse
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(self.driver)
                actions.move_by_offset(random.randint(100, 300), random.randint(100, 200))
                actions.perform()
                time.sleep(random.uniform(0.5, 1.5))
            except Exception:
                pass

            # 3. Procura campo de busca e digita como humano
            try:
                search_box = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.NAME, "q"))
                )

                # Clica no campo
                search_box.click()
                time.sleep(random.uniform(0.3, 0.8))

                # Digitação humana (letra por letra com delays)
                for char in term:
                    search_box.send_keys(char)
                    time.sleep(self.human_behavior.typing_delay())

                time.sleep(random.uniform(0.5, 1.2))

                # Pressiona Enter
                from selenium.webdriver.common.keys import Keys
                search_box.send_keys(Keys.RETURN)

            except Exception as e:
                print(f"    [DEBUG] Erro na busca interativa, usando URL direta: {str(e)[:30]}")
                # Fallback para método direto
                import urllib.parse
                encoded_term = urllib.parse.quote_plus(term)
                search_url = f"https://www.google.com/search?q={encoded_term}&hl=pt-BR&gl=BR"
                self.driver.get(search_url)

            # Simula tempo de leitura dos resultados
            self.human_behavior.random_delay(2.0, 4.0)

            # Incrementa contador de buscas
            self.searches_count += 1

            # Verifica se precisa de pausa de sessão
            if self.human_behavior.session_break_needed(self.searches_count):
                self.human_behavior.take_session_break()

            # Verifica se carregou resultados
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.g, div.tF2Cxc, #search"))
                )

                # Verifica se não é CAPTCHA
                if "captcha" in self.driver.page_source.lower() or "unusual traffic" in self.driver.page_source.lower():
                    print("    [AVISO] CAPTCHA detectado! Tentando fallback...")
                    return self._fallback_search_simple(term)

                return True

            except Exception as e:
                print(f"    [DEBUG] Timeout na busca, tentando fallback: {str(e)[:30]}")
                return self._fallback_search_simple(term)

        except Exception as e:
            print(f"[ERRO] Falha na busca Google: {e}")
            return False

    def _fallback_search_simple(self, term):
        """Fallback simples que retorna True/False"""
        try:
            ddg_url = f"https://duckduckgo.com/?q={term.replace(' ', '+')}"
            self.driver.get(ddg_url)
            time.sleep(random.uniform(*self.delays["page_load"]))
            return True
        except Exception as e:
            print(f"    [DEBUG] Erro no fallback: {str(e)[:30]}")
            return False

    def get_result_links(self, blacklist_hosts):
        """Retorna links dos resultados da página atual"""
        urls = []

        # Scroll humano para carregar mais resultados
        self.human_behavior.scroll_behavior(self.driver)

        # Movimento de mouse ocasional
        if random.random() < 0.3:  # 30% chance
            self.human_behavior.mouse_movement(self.driver)

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
                    except Exception as e:
                        print(f"    [DEBUG] Erro ao processar link: {str(e)[:30]}")
                        continue
                if urls:
                    break
            except Exception as e:
                print(f"    [DEBUG] Erro no seletor: {str(e)[:30]}")
                continue

        return urls

    @RetryManager.with_retry(max_attempts=2, base_delay=1.5, exceptions=(WebDriverException, TimeoutException))
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
                    new_start = current_start + SECOND_PAGE_START
                    new_url = re.sub(r'&start=\d+', f'&start={new_start}', current_url)
                else:
                    new_url = current_url + f"&start={SECOND_PAGE_START}"
            else:
                # Adiciona start=10 para segunda página
                new_url = current_url + f"&start={SECOND_PAGE_START}"

            self.driver.get(new_url)
            time.sleep(random.uniform(*self.delays["page_load"]))

            # Verifica se carregou resultados
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.g, div.tF2Cxc"))
                )
                return True
            except Exception as e:
                print(f"    [DEBUG] Erro ao verificar próxima página: {str(e)[:30]}")
                return False

        except Exception as e:
            print(f"    [AVISO] Falha ao ir para próxima página: {str(e)[:MAX_ERROR_URL_LENGTH]}")
            return False

    @RetryManager.with_retry(max_attempts=2, base_delay=1.0, exceptions=(WebDriverException, TimeoutException))
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

            # Simula tempo de leitura da página
            page_title = self.driver.title or ""
            reading_time = self.human_behavior.reading_delay(len(page_title))
            time.sleep(min(reading_time, 3.0))  # Máximo 3s

            # Scroll humano para carregar conteúdo
            self.human_behavior.scroll_behavior(self.driver)

            # Movimento de mouse ocasional
            if random.random() < 0.4:  # 40% chance
                self.human_behavior.mouse_movement(self.driver)

            # Capturar HTML content e extrair endereço formatado
            html_content = self.driver.page_source

            # Extrair endereço formatado usando AddressExtractor
            from src.infrastructure.utils.address_extractor import AddressExtractor
            endereco_formatado = AddressExtractor.extract_from_html(html_content)

            # Extração rápida de e-mails
            page_source = html_content

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
                    if self.validation_service.is_valid_email(clean_email) and clean_email not in [e.lower() for e in
                                                                                                   emails]:
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
                name = name.strip()[:MAX_TITLE_LENGTH]  # Limita tamanho
            except Exception as e:
                print(f"    [DEBUG] Erro ao obter título: {str(e)[:30]}")
                name = url.split('/')[2]

            return CompanyModel(
                name=name,
                emails=emails_string,
                domain=url.split('/')[2] if '/' in url else url,
                url=url,
                address=endereco_formatado or "",
                phone=phones_string,
                html_content=html_content
            )

        except Exception as e:
            print(f"[ERRO] Falha ao extrair dados de {url}: {str(e)[:MAX_ERROR_MESSAGE_LENGTH]}")
            return CompanyModel(
                name="",
                emails="",
                domain=url.split('/')[2] if '/' in url else url,
                url=url,
                address="",
                phone="",
                html_content=""
            )
        finally:
            # Fecha aba atual e volta para aba de resultados (igual ao DuckDuckGo)
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except Exception as e:
                print(f"[DEBUG] Erro ao fechar janela: {str(e)[:30]}")

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
                        if len(phones) >= MAX_PHONES_PER_SITE:
                            break
                if len(phones) >= MAX_PHONES_PER_SITE:
                    break
        except Exception as e:
            print(f"    [DEBUG] Erro ao extrair telefones: {str(e)[:30]}")

        return list(phones)
