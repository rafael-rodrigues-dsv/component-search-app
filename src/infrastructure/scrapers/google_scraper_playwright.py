"""
Google Scraper Playwright - Versão otimizada com Playwright
"""
import random
import time
import re
from typing import List

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from src.infrastructure.config.config_manager import ConfigManager
from src.infrastructure.config.delay_config import get_scraper_delays
from ...domain.models.company_model import CompanyModel
from ...domain.services.email_domain_service import EmailValidationService


class GoogleScraperPlaywright:
    """Scraper do Google usando Playwright"""

    def __init__(self, page: Page):
        self.page = page
        self.base_url = "https://www.google.com"
        self.validation_service = EmailValidationService()
        self.searches_count = 0
        self.delays = get_scraper_delays("GOOGLE")
        self.config = ConfigManager()

    def search(self, term, max_results=50):
        """Executa busca no Google"""
        try:
            print(f"[GOOGLE] 🔍 Iniciando busca: '{term}'")
            print(f"[GOOGLE] 🌐 Acessando google.com...")

            self.page.goto("https://www.google.com", wait_until='domcontentloaded', timeout=10000)
            time.sleep(random.uniform(1.0, 2.0))

            print(f"[GOOGLE] ⌨️  Digitando termo...")

            # Tentar múltiplos seletores para o campo de busca
            search_selectors = [
                'input[name="q"]',
                'textarea[name="q"]',
                '#APjFqb',
                'textarea.gLFyf',
                'input[type="text"]'
            ]

            typed = False
            for selector in search_selectors:
                try:
                    self.page.fill(selector, term, timeout=5000)
                    time.sleep(random.uniform(0.3, 0.6))
                    self.page.press(selector, 'Enter')
                    typed = True
                    break
                except:
                    continue

            if not typed:
                print(f"[GOOGLE] ❌ Campo de busca não encontrado")
                return False

            print(f"[GOOGLE] ✅ Busca executada")

            try:
                self.page.wait_for_selector('div.g, div.tF2Cxc, #search', timeout=10000)
                print(f"[GOOGLE] ✅ Resultados carregados")
                return True
            except PlaywrightTimeoutError:
                print(f"[GOOGLE] ⏱️  Timeout aguardando resultados")
                return False

        except Exception as e:
            print(f"[GOOGLE] ❌ Erro: {str(e)[:100]}")
            return False

    def get_result_links(self, blacklist_hosts: List[str]) -> List[str]:
        """Extrai links dos resultados"""
        print(f"[GOOGLE] 🔗 Coletando links...")
        urls = []

        try:
            self.page.mouse.wheel(0, 1000)
            time.sleep(random.uniform(*self.delays["scroll"]))

            selectors = [
                "div.g a[href]:not([href*='google.com'])",
                "div.tF2Cxc a[href]:not([href*='google.com'])",
                "h3 a[href]:not([href*='google.com'])"
            ]

            for selector in selectors:
                try:
                    elements = self.page.locator(selector).all()
                    for elem in elements:
                        try:
                            if elem.is_visible():
                                url = elem.get_attribute("href")
                                if url and self._is_valid_url(url):
                                    domain = url.split('/')[2].lower()
                                    if not any(host in domain for host in blacklist_hosts):
                                        urls.append(url)
                        except:
                            continue
                    if urls:
                        break
                except:
                    continue

            print(f"[GOOGLE] ✅ {len(urls)} links encontrados")
        except Exception as e:
            print(f"[GOOGLE] ⚠️  Erro ao coletar links: {str(e)[:50]}")

        return urls

    def go_to_next_page(self):
        """Navega para próxima página"""
        try:
            current_url = self.page.url

            if "&start=" in current_url:
                start_match = re.search(r'&start=(\d+)', current_url)
                if start_match:
                    current_start = int(start_match.group(1))
                    new_start = current_start + 10
                    new_url = re.sub(r'&start=\d+', f'&start={new_start}', current_url)
                else:
                    new_url = current_url + "&start=10"
            else:
                new_url = current_url + "&start=10"

            self.page.goto(new_url, wait_until='domcontentloaded')
            time.sleep(random.uniform(*self.delays["page_load"]))

            try:
                self.page.wait_for_selector("div.g, div.tF2Cxc", timeout=5000)
                return True
            except:
                return False

        except Exception:
            return False

    def extract_company_data(self, url, max_emails):
        """Extrai dados da empresa"""
        new_page = None
        try:
            print(f"[COLETA] 🌐 Acessando: {url[:60]}...")

            new_page = self.page.context.new_page()
            new_page.goto(url, timeout=5000, wait_until='domcontentloaded')

            time.sleep(random.uniform(0.5, 1.0))
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

            domain = url.split('/')[2] if '/' in url else url
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
                domain=url.split('/')[2] if '/' in url else url,
                url=url,
                address="",
                phone="",
                html_content=""
            )
        finally:
            if new_page:
                try:
                    new_page.close()
                    print(f"[COLETA] ↩️  Voltou para busca")
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
