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

from src.infrastructure.config.config_manager import ConfigManager
from src.infrastructure.config.delay_config import get_scraper_delays
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
            print(f"[DUCKGO] 🔍 Iniciando busca: '{query}'")
            print(f"[DUCKGO] 🌐 Acessando duckduckgo.com...")
            self.driver_manager.driver.get("https://duckduckgo.com/")

            print(f"[DUCKGO] ⌨️  Digitando termo...")
            search_box = WebDriverWait(self.driver_manager.driver, 10).until(
                EC.presence_of_element_located((By.ID, "searchbox_input"))
            )

            search_box.clear()
            search_box.send_keys(query)
            search_box.send_keys(Keys.ENTER)

            print(f"[DUCKGO] ⏳ Aguardando resultados...")
            # Timeout aumentado: 10s → 15s (igual ao Google)
            try:
                WebDriverWait(self.driver_manager.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='result']"))
                )

                time.sleep(random.uniform(*self.delays["page_load"]))
                print(f"[DUCKGO] ✅ Busca executada")
                return True

            except TimeoutException:
                print(f"[DUCKGO] ⏱️  Timeout aguardando resultados (15s)")
                print(f"[DUCKGO] 🔄 Tentando método direto como fallback...")

                # Fallback: URL direta
                try:
                    direct_url = f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
                    self.driver_manager.driver.get(direct_url)
                    time.sleep(3)

                    # Verificar se carregou
                    if len(self.driver_manager.driver.page_source) > 5000:
                        print(f"[DUCKGO] ✅ Método direto funcionou")
                        return True
                except Exception:
                    pass

                # Fallback final: tentar Google
                print(f"[DUCKGO] 🔄 DuckDuckGo falhou, tentando Google como fallback...")
                return self._fallback_to_google(query)

        except Exception as e:
            print(f"[DUCKGO] ❌ Erro na busca: {str(e)[:50]}")
            # Tentar Google como último recurso
            return self._fallback_to_google(query)

    def _fallback_to_google(self, query: str) -> bool:
        """Fallback para Google quando DuckDuckGo falha"""
        try:
            print(f"[DUCKGO] 📍 Usando Google como fallback...")
            import urllib.parse
            encoded_query = urllib.parse.quote_plus(query)
            google_url = f"https://www.google.com/search?q={encoded_query}&hl=pt-BR&gl=BR"

            self.driver_manager.driver.get(google_url)
            time.sleep(random.uniform(3.0, 5.0))

            # Verificar se carregou
            if len(self.driver_manager.driver.page_source) > 5000:
                print(f"[DUCKGO] ✅ Fallback Google funcionou")
                return True

            print(f"[DUCKGO] ❌ Todos fallbacks falharam")
            return False

        except Exception as e:
            print(f"[DUCKGO] ❌ Fallback Google falhou: {str(e)[:50]}")
            return False

    def get_result_links(self, blacklist_hosts: List[str]) -> List[str]:
        """Extrai links rapidamente"""
        print(f"[DUCKGO] 🔗 Coletando links...")
        links = []
        try:
            # Scroll para carregar mais resultados
            self.driver_manager.driver.execute_script("window.scrollBy(0, 1500);")
            time.sleep(random.uniform(*self.delays["scroll"]))

            # Aguarda elementos carregarem
            WebDriverWait(self.driver_manager.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='result']"))
            )
            
            cards = self.driver_manager.driver.find_elements(By.CSS_SELECTOR, "[data-testid='result']")
            for card in cards:
                try:
                    # Verifica se o elemento ainda é válido
                    if card.is_displayed():
                        link_elements = card.find_elements(By.CSS_SELECTOR, "a[data-testid='result-title-a']")
                        
                        if link_elements and link_elements[0].is_displayed():
                            href = link_elements[0].get_attribute("href") or ""
                            if href.startswith("http") and not self._is_blacklisted(href, blacklist_hosts):
                                links.append(href)
                except Exception:
                    # Ignora elementos que se tornaram stale
                    continue
                    
        except Exception:
            # Falha silenciosa - não imprime erro pois é esperado
            pass

        print(f"[DUCKGO] ✅ {len(links)} links encontrados")
        return list(set(links))  # Remove duplicatas

    def go_to_next_page(self):
        """Navega para a próxima página de resultados"""
        try:
            print(f"[DUCKGO] ➡️  Carregando mais resultados...")
            # Scroll progressivo para carregar mais resultados (DuckDuckGo usa lazy loading)
            initial_results = len(self.driver_manager.driver.find_elements(By.CSS_SELECTOR, "[data-testid='result']"))
            
            # Scroll até o final da página
            self.driver_manager.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(*self.delays["scroll"]))
            
            # Aguarda carregamento dinâmico
            time.sleep(2)
            
            # Scroll adicional para garantir carregamento
            for i in range(3):
                self.driver_manager.driver.execute_script("window.scrollBy(0, 1000);")
                time.sleep(random.uniform(*self.delays["scroll"]))
                
                # Verifica se novos resultados foram carregados
                current_results = len(self.driver_manager.driver.find_elements(By.CSS_SELECTOR, "[data-testid='result']"))
                if current_results > initial_results:
                    print(f"[DUCKGO] ✅ +{current_results - initial_results} novos resultados")
                    return True
            
            # Scroll final para garantir que carregou tudo
            self.driver_manager.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            
            print(f"[DUCKGO] ✅ Scroll completo")
            return True  # Sempre retorna True pois DuckDuckGo carrega via scroll

        except Exception as e:
            print(f"[DUCKGO] ⚠️  Erro no scroll: {str(e)[:50]}")
            return False

    def extract_company_data(self, url: str, max_emails: int) -> CompanyModel:
        """Extração otimizada de dados da empresa usando sistema de abas"""
        try:
            print(f"[COLETA] 🌐 Acessando: {url[:60]}...")

            # Abre site em nova aba (mantém aba de pesquisa aberta)
            self.driver_manager.driver.execute_script("window.open(arguments[0],'_blank');", url)
            self.driver_manager.driver.switch_to.window(self.driver_manager.driver.window_handles[-1])
            
            # Timeout otimizado - 3 segundos máximo
            self.driver_manager.driver.set_page_load_timeout(3)
            
            try:
                # Aguarda carregamento mínimo
                WebDriverWait(self.driver_manager.driver, 3).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                # Continua silenciosamente - timeout é esperado
                pass

            # Para carregamento forçadamente
            try:
                self.driver_manager.driver.execute_script("window.stop();")
            except:
                pass

            time.sleep(1)  # Delay fixo mínimo

            # Scroll mínimo
            self.driver_manager.driver.execute_script("window.scrollTo(0, 1000);")
            time.sleep(1)

            print(f"[COLETA] 📄 Capturando HTML...")
            # Capturar HTML (limitado para performance)
            html_content = self.driver_manager.driver.page_source
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
            name = self._get_company_name_fast(url)
            domain = self.validation_service.extract_domain_from_url(url)
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
            return CompanyModel(name="", emails="", domain="", url=url, html_content="")
        finally:
            # Fecha aba atual e volta para aba de pesquisa
            try:
                if len(self.driver_manager.driver.window_handles) > 1:
                    self.driver_manager.driver.close()
                    self.driver_manager.driver.switch_to.window(self.driver_manager.driver.window_handles[0])
                    print(f"[COLETA] ↩️  Voltou para busca")
            except Exception as e:
                print(f"[COLETA] ⚠️  Erro ao fechar aba: {str(e)[:40]}")

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
            print(f"[COLETA] ⚠️  Erro ao obter título: {str(e)[:30]}")

        return self.validation_service.extract_domain_from_url(url)

    def _is_blacklisted(self, url: str, blacklist_hosts: List[str]) -> bool:
        """Verifica se URL está na blacklist"""
        url_lower = url.lower()
        return any(host in url_lower for host in blacklist_hosts)
