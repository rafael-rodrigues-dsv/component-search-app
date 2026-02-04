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

from src.infrastructure.config.config_manager import ConfigManager
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
        self.config = ConfigManager()  # Para acessar configurações de retry

    def search(self, term, max_results=50):
        @RetryManager.with_retry(
            max_attempts=self.config.retry_max_attempts,
            base_delay=self.config.retry_base_delay,
            backoff_factor=self.config.retry_backoff_factor,
            max_delay=self.config.retry_max_delay,
            exceptions=(WebDriverException, TimeoutException)
        )
        def _search_impl():
            return self._search_implementation(term, max_results)
        return _search_impl()
    
    def _search_implementation(self, term, max_results=50):
        """Executa busca no Google simulando comportamento humano"""
        try:
            print(f"[GOOGLE] 🔍 Iniciando busca: '{term}'")

            # === NAVEGAÇÃO HUMANA ===
            # 1. Primeiro vai para Google.com (como humano faria)
            print(f"[GOOGLE] 🌐 Acessando google.com...")
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
                print(f"[GOOGLE] ⌨️  Digitando termo...")
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
                print(f"[GOOGLE] ✅ Busca executada")

            except Exception as e:
                print(f"[GOOGLE] ⚠️  Busca interativa falhou, usando URL direta")
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

            # Verifica se carregou resultados (timeout aumentado + mais seletores)
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR,
                        "div.g, div.tF2Cxc, #search, #rso, .hlcw0c, #rcnt"
                    ))
                )

                # Verifica se não é CAPTCHA
                page_lower = self.driver.page_source.lower()
                if "captcha" in page_lower or "unusual traffic" in page_lower:
                    print(f"[GOOGLE] ⚠️  CAPTCHA detectado! Usando fallback...")
                    return self._fallback_search_simple(term)

                print(f"[GOOGLE] ✅ Resultados carregados")
                return True

            except TimeoutException:
                print(f"[GOOGLE] ⏱️  Timeout aguardando resultados (15s)")
                # Tentar fallback antes de falhar
                print(f"[GOOGLE] 🔄 Tentando método direto como fallback...")
                try:
                    import urllib.parse
                    encoded_term = urllib.parse.quote_plus(term)
                    search_url = f"https://www.google.com/search?q={encoded_term}&hl=pt-BR&gl=BR"
                    self.driver.get(search_url)
                    time.sleep(3)

                    # Verificar se carregou agora
                    if len(self.driver.page_source) > 5000:
                        print(f"[GOOGLE] ✅ Método direto funcionou")
                        return True
                except Exception:
                    pass

                print(f"[GOOGLE] ❌ Todas tentativas falharam, usando DuckDuckGo...")
                return self._fallback_search_simple(term)

            except Exception as e:
                print(f"[GOOGLE] ❌ Erro: {str(e)[:50]}")
                return self._fallback_search_simple(term)

        except Exception as e:
            print(f"[ERRO] Falha na busca Google: {e}")
            return False

    def _fallback_search_simple(self, term):
        """Fallback robusto: tenta Google direto, depois DuckDuckGo"""
        print(f"[GOOGLE] 🔄 Executando fallback...")

        # Tentativa 1: Google com URL direta (sem cookies)
        try:
            print(f"[GOOGLE] 📍 Tentativa 1: Google URL direta...")
            import urllib.parse
            encoded_term = urllib.parse.quote_plus(term)
            search_url = f"https://www.google.com/search?q={encoded_term}&hl=pt-BR&gl=BR"

            self.driver.get(search_url)
            time.sleep(random.uniform(3.0, 5.0))

            # Verificar se carregou resultados
            if len(self.driver.page_source) > 5000 and "google" in self.driver.current_url.lower():
                print(f"[GOOGLE] ✅ Fallback Google funcionou")
                return True

        except Exception as e:
            print(f"[GOOGLE] ⚠️  Fallback Google falhou: {str(e)[:40]}")

        # Tentativa 2: DuckDuckGo (último recurso)
        try:
            print(f"[GOOGLE] 📍 Tentativa 2: DuckDuckGo como último recurso...")
            ddg_url = f"https://duckduckgo.com/?q={term.replace(' ', '+')}"
            self.driver.get(ddg_url)
            time.sleep(random.uniform(*self.delays["page_load"]))

            print(f"[GOOGLE] ✅ Fallback DuckDuckGo funcionou")
            return True

        except Exception as e:
            print(f"[GOOGLE] ❌ Todos fallbacks falharam: {str(e)[:40]}")
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
                        # Verifica se elemento ainda é válido
                        if link.is_displayed():
                            url = link.get_attribute("href")
                            if url and self._is_valid_url(url):
                                # Verifica blacklist
                                domain = url.split('/')[2].lower()
                                if not any(host in domain for host in blacklist_hosts):
                                    urls.append(url)
                    except Exception:
                        # Ignora elementos stale silenciosamente
                        continue
                if urls:
                    break
            except Exception:
                # Falha silenciosa no seletor
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
            print(f"    [INFO] Carregando site: {url}")
            
            # Abre site em nova aba (igual ao DuckDuckGo)
            self.driver.execute_script("window.open(arguments[0],'_blank');", url)
            self.driver.switch_to.window(self.driver.window_handles[-1])

            # Timeout otimizado - 5 segundos máximo
            self.driver.set_page_load_timeout(5)
            
            try:
                # Aguarda carregamento mínimo
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                # Continua silenciosamente - timeout é esperado
                pass

            # Para carregamento forçadamente se necessário
            try:
                self.driver.execute_script("window.stop();")
            except:
                pass

            # Simula tempo de leitura da página
            page_title = self.driver.title or ""
            reading_time = self.human_behavior.reading_delay(len(page_title))
            time.sleep(min(reading_time, 3.0))  # Máximo 3s

            print(f"    [DEBUG] Fazendo scroll...")
            # Scroll humano para carregar conteúdo
            self.human_behavior.scroll_behavior(self.driver)

            # Movimento de mouse ocasional
            if random.random() < 0.4:  # 40% chance
                self.human_behavior.mouse_movement(self.driver)

            print(f"[COLETA] 📄 Capturando HTML...")
            # Capturar HTML content (limitado para performance)
            html_content = self.driver.page_source
            if len(html_content) > 100000:  # Limita a 100KB
                html_content = html_content[:100000]
            print(f"[COLETA] ✅ HTML: {len(html_content):,} chars")

            # === EXTRAÇÃO AVANÇADA DE DADOS ===
            print(f"[COLETA] 🔍 Extraindo dados com bibliotecas especializadas...")
            try:
                from src.infrastructure.services.advanced_extraction_service import get_advanced_extraction_service
                extraction_service = get_advanced_extraction_service()

                # Extrair tudo de uma vez
                emails, phones, address = extraction_service.extract_all(
                    html_content,
                    max_emails=max_emails,
                    max_phones=2
                )

                # Converter para formato esperado
                emails_string = self.validation_service.validate_and_join_emails(emails)
                phones_string = self.validation_service.validate_and_join_phones(phones)
                endereco_formatado = address if address else None

                print(f"[COLETA] 📧 Emails: {len(emails)} encontrados")
                print(f"[COLETA] 📞 Telefones: {len(phones)} encontrados")
                if endereco_formatado:
                    print(f"[COLETA] 📍 Endereço: {endereco_formatado[:50]}...")
                else:
                    print(f"[COLETA] ⚠️  Endereço não encontrado")

            except Exception as e:
                print(f"[COLETA] ⚠️  Erro na extração avançada: {str(e)[:50]}, usando fallback...")
                emails_string = ""
                phones_string = ""
                endereco_formatado = None

            print(f"[COLETA] 🏢 Extraindo nome da empresa...")
            # Nome da empresa (título da página)
            try:
                name = self.driver.title or url.split('/')[2]
                name = name.strip()[:MAX_TITLE_LENGTH]  # Limita tamanho
            except Exception as e:
                print(f"[COLETA] ⚠️  Erro ao obter título: {str(e)[:30]}")
                name = url.split('/')[2]
            
            domain = url.split('/')[2] if '/' in url else url
            print(f"[COLETA] ✅ {name[:40]}... | {domain}")

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
            print(f"[COLETA] ❌ Erro: {str(e)[:60]}")
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
            # Fecha aba atual e volta para aba de pesquisa
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    print(f"[COLETA] ↩️  Voltou para busca")
            except Exception as e:
                print(f"[COLETA] ⚠️  Erro ao fechar aba: {str(e)[:40]}")

    def _is_valid_url(self, url):
        """Verifica se URL é válida"""
        if not url or not url.startswith("http"):
            return False

        invalid_patterns = [
            "google.com", "youtube.com", "maps.google", "translate.google"
        ]

        return not any(pattern in url.lower() for pattern in invalid_patterns)

    def _extract_emails_fast(self, html_content: str) -> list:
        """Extração ultra-rápida de e-mails"""
        emails = set()

        try:
            # Regex otimizada
            import re
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

    def _extract_phones_fast(self, page_source) -> list:
        """Extração ultra-rápida de telefones"""
        phones = set()

        try:
            # Padrão otimizado para telefones brasileiros
            import re
            phone_pattern = r'(?:\([1-9][1-9]\)\s?|[1-9][1-9]\s)[9][0-9]{4}[-\s]?[0-9]{4}|(?:\([1-9][1-9]\)\s?|[1-9][1-9]\s)[2-5][0-9]{3}[-\s]?[0-9]{4}'
            found_phones = re.findall(phone_pattern, page_source)

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
            title = self.driver.title or ""
            if title.strip():
                return title.strip()[:50]
        except Exception as e:
            print(f"[DEBUG] Erro ao obter nome da empresa: {str(e)[:30]}")

        return self.validation_service.extract_domain_from_url(url)
