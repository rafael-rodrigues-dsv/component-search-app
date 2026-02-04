"""
DuckDuckGo Scraper Playwright - Versão otimizada com Playwright
"""
import random
import time
from typing import List

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from src.infrastructure.config.config_manager import ConfigManager
from src.infrastructure.config.delay_config import get_scraper_delays
from ...domain.models.company_model import CompanyModel
from ...domain.services.email_domain_service import EmailValidationService


class DuckDuckGoScraperPlaywright:
    """Scraper do DuckDuckGo usando Playwright"""

    def __init__(self, page: Page):
        self.page = page
        self.validation_service = EmailValidationService()
        self.delays = get_scraper_delays("DUCKDUCKGO")
        self.config = ConfigManager()

    def search(self, query: str, max_retries: int = 2) -> bool:
        """Executa busca no DuckDuckGo"""
        try:
            print(f"[DUCKGO] 🔍 Iniciando busca: '{query}'")
            print(f"[DUCKGO] 🌐 Acessando duckduckgo.com...")

            self.page.goto("https://duckduckgo.com/", wait_until='domcontentloaded', timeout=10000)

            print(f"[DUCKGO] ⌨️  Digitando termo...")

            # Tentar múltiplos seletores para o campo de busca
            search_selectors = [
                '#searchbox_input',
                'input[name="q"]',
                'input[type="text"]',
                '#search_form_input'
            ]

            typed = False
            for selector in search_selectors:
                try:
                    self.page.fill(selector, query, timeout=5000)
                    time.sleep(random.uniform(0.2, 0.4))
                    self.page.press(selector, 'Enter')
                    typed = True
                    break
                except:
                    continue

            if not typed:
                print(f"[DUCKGO] ❌ Campo de busca não encontrado")
                return False

            print(f"[DUCKGO] ⏳ Aguardando resultados...")

            try:
                self.page.wait_for_selector('[data-testid="result"]', timeout=10000)
                time.sleep(random.uniform(*self.delays["page_load"]))
                print(f"[DUCKGO] ✅ Busca executada")
                return True
            except PlaywrightTimeoutError:
                print(f"[DUCKGO] ⏱️  Timeout aguardando resultados")
                return False

        except Exception as e:
            print(f"[DUCKGO] ❌ Erro: {str(e)[:100]}")
            return False

    def get_result_links(self, blacklist_hosts: List[str]) -> List[str]:
        """Extrai links dos resultados"""
        print(f"[DUCKGO] 🔗 Coletando links...")
        links = []

        try:
            self.page.mouse.wheel(0, 1500)
            time.sleep(random.uniform(*self.delays["scroll"]))

            self.page.wait_for_selector('[data-testid="result"]', timeout=5000)

            cards = self.page.locator('[data-testid="result"]').all()
            for card in cards:
                try:
                    if card.is_visible():
                        link_elem = card.locator('a[data-testid="result-title-a"]').first
                        if link_elem:
                            href = link_elem.get_attribute("href") or ""
                            if href.startswith("http") and not self._is_blacklisted(href, blacklist_hosts):
                                links.append(href)
                except:
                    continue

            print(f"[DUCKGO] ✅ {len(links)} links encontrados")
        except:
            pass

        return list(set(links))

    def go_to_next_page(self):
        """Navega para próxima página (scroll para carregar mais)"""
        try:
            print(f"[DUCKGO] ➡️  Carregando mais resultados...")

            initial_results = len(self.page.locator('[data-testid="result"]').all())

            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(random.uniform(*self.delays["scroll"]))

            time.sleep(2)

            for i in range(3):
                self.page.mouse.wheel(0, 1000)
                time.sleep(random.uniform(*self.delays["scroll"]))

                current_results = len(self.page.locator('[data-testid="result"]').all())
                if current_results > initial_results:
                    print(f"[DUCKGO] ✅ +{current_results - initial_results} novos resultados")
                    return True

            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)

            print(f"[DUCKGO] ✅ Scroll completo")
            return True

        except Exception as e:
            print(f"[DUCKGO] ⚠️  Erro no scroll: {str(e)[:50]}")
            return False

    def extract_company_data(self, url: str, max_emails: int) -> CompanyModel:
        """Extrai dados da empresa"""
        new_page = None
        try:
            print(f"[COLETA] 🌐 Acessando: {url[:60]}...")

            new_page = self.page.context.new_page()
            new_page.goto(url, timeout=3000, wait_until='domcontentloaded')

            time.sleep(0.5)
            new_page.mouse.wheel(0, 1000)

            print(f"[COLETA] 📄 Capturando HTML...")
            html_content = new_page.content()
            if len(html_content) > 100000:
                html_content = html_content[:100000]
            print(f"[COLETA] ✅ HTML: {len(html_content):,} chars")

            print(f"[COLETA] 🔍 Extraindo dados...")
            from src.infrastructure.services.advanced_extraction_service import get_advanced_extraction_service
            extraction_service = get_advanced_extraction_service()

            emails, phones, address = extraction_service.extract_all(
                html_content,
                max_emails=max_emails,
                max_phones=2
            )

            emails_string = self.validation_service.validate_and_join_emails(emails)
            phones_string = self.validation_service.validate_and_join_phones(phones)

            print(f"[COLETA] 📧 Emails: {len(emails)} encontrados")
            print(f"[COLETA] 📞 Telefones: {len(phones)} encontrados")
            if address:
                print(f"[COLETA] 📍 Endereço: {address[:50]}...")

            print(f"[COLETA] 🏢 Extraindo nome da empresa...")
            name = new_page.title() or url.split('/')[2]
            name = name.strip()[:50]

            domain = self.validation_service.extract_domain_from_url(url)
            print(f"[COLETA] ✅ {name[:40]}... | {domain}")

            return CompanyModel(
                name=name,
                emails=emails_string,
                domain=domain,
                url=url,
                address=address or "",
                phone=phones_string,
                html_content=html_content
            )

        except Exception as e:
            print(f"[COLETA] ❌ Erro: {str(e)[:60]}")
            return CompanyModel(
                name="",
                emails="",
                domain="",
                url=url,
                html_content=""
            )
        finally:
            if new_page:
                try:
                    new_page.close()
                    print(f"[COLETA] ↩️  Voltou para busca")
                except:
                    pass

    def _is_blacklisted(self, url: str, blacklist_hosts: List[str]) -> bool:
        """Verifica se URL está na blacklist"""
        try:
            domain = url.split('/')[2].lower()
            return any(host in domain for host in blacklist_hosts)
        except:
            return True
