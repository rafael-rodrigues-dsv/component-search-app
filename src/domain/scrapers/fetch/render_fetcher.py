"""
Render Fetcher - Wrapper para Playwright (renderização sob demanda)
"""
from typing import Optional
from ..utils.scraper_logger import ScraperLogger


class RenderFetcher:
    """
    Fetcher com renderização JavaScript usando Playwright

    Usado quando HTML puro não é suficiente (SPAs, conteúdo dinâmico)
    """

    def __init__(self, logger: Optional[ScraperLogger] = None, headless: bool = True):
        """
        Args:
            logger: Logger opcional
            headless: True = invisível (padrão), False = visível
        """
        self.logger = logger or ScraperLogger('RENDER_FETCHER')
        self.headless = headless  # 🆕 Configurável
        self.page = None
        self.browser = None
        self.context = None

    def render(self, url: str, timeout: int = 10000, wait_until: str = 'domcontentloaded') -> Optional[str]:
        """
        Renderiza página com Playwright

        Args:
            url: URL para renderizar
            timeout: Timeout em milissegundos
            wait_until: Condição de espera ('load', 'domcontentloaded', 'networkidle')

        Returns:
            HTML renderizado ou None em caso de erro
        """
        try:
            from playwright.sync_api import sync_playwright

            self.logger.log('web', f"Renderizando com Playwright: {url[:60]}...")

            with sync_playwright() as p:
                # 🆕 Lançar browser (headless configurável)
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = context.new_page()

                # Navegar
                page.goto(url, timeout=timeout, wait_until=wait_until)

                # Aguardar um pouco para JS carregar
                page.wait_for_timeout(1000)

                # Capturar HTML
                html = page.content()

                self.logger.log('success', f"Renderizado: {len(html):,} chars")

                # Fechar
                page.close()
                context.close()
                browser.close()

                return html

        except ImportError:
            self.logger.log('error', "Playwright não instalado")
            return None

        except Exception as e:
            self.logger.log('error', f"Erro ao renderizar: {str(e)[:50]}")
            return None

    def render_with_scroll(self, url: str, scroll_times: int = 3) -> Optional[str]:
        """
        Renderiza página e faz scroll para carregar conteúdo lazy-load

        Args:
            url: URL para renderizar
            scroll_times: Número de vezes para fazer scroll

        Returns:
            HTML renderizado
        """
        try:
            from playwright.sync_api import sync_playwright

            self.logger.log('web', f"Renderizando com scroll: {url[:60]}...")

            with sync_playwright() as p:
                # 🆕 Usar self.headless
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context()
                page = context.new_page()

                page.goto(url, timeout=10000, wait_until='domcontentloaded')

                # Fazer scroll múltiplas vezes
                for i in range(scroll_times):
                    page.mouse.wheel(0, 1000)
                    page.wait_for_timeout(500)

                html = page.content()

                page.close()
                context.close()
                browser.close()

                self.logger.log('success', f"Renderizado com scroll: {len(html):,} chars")

                return html

        except Exception as e:
            self.logger.log('error', f"Erro: {str(e)[:50]}")
            return None
