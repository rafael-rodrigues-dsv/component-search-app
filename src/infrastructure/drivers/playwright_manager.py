"""
Playwright Manager - Gerenciador de browser Playwright
"""
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
from typing import Optional
import random
import subprocess
import sys


class PlaywrightManager:
    """Gerenciador de Playwright (substitui WebDriverManager)"""

    def __init__(self, headless: bool = True, browser_type: str = "chromium"):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.headless = headless

        # Mapear escolha do usuário para browser Playwright
        # CHROME/BRAVE -> chromium
        # Futuramente: FIREFOX -> firefox, EDGE -> webkit
        if browser_type.upper() in ["CHROME", "BRAVE"]:
            self.browser_type = "chromium"
        elif browser_type.upper() == "FIREFOX":
            self.browser_type = "firefox"
        elif browser_type.upper() in ["EDGE", "WEBKIT"]:
            self.browser_type = "webkit"
        else:
            self.browser_type = browser_type.lower()  # Usar como está

    def _ensure_browser_installed(self):
        """Garante que o browser está instalado (auto-instalação se necessário)"""
        try:
            test_playwright = sync_playwright().start()
            browser_launcher = getattr(test_playwright, self.browser_type)
            test_browser = browser_launcher.launch(headless=True)
            test_browser.close()
            test_playwright.stop()
            return True
        except Exception as e:
            error_msg = str(e).lower()
            if 'executable' in error_msg or 'not found' in error_msg or 'browser' in error_msg:
                browser_name = self.browser_type.capitalize()
                print(f"\n[PLAYWRIGHT] 📦 Browser {browser_name} não encontrado!")
                print(f"[PLAYWRIGHT] 🔧 Instalando automaticamente (primeira vez, ~100MB, 1-2 min)...")

                try:
                    result = subprocess.run(
                        [sys.executable, '-m', 'playwright', 'install', self.browser_type],
                        capture_output=True,
                        timeout=300,
                        text=True
                    )

                    if result.returncode == 0:
                        print(f"[PLAYWRIGHT] ✅ Browser {browser_name} instalado com sucesso!")
                        return True
                    else:
                        print(f"[PLAYWRIGHT] ❌ Erro ao instalar: {result.stderr}")
                        return False
                except Exception as install_error:
                    print(f"[PLAYWRIGHT] ❌ Erro na instalação: {install_error}")
                    return False
            else:
                raise

    def start(self):
        """Inicializa Playwright com anti-detecção"""
        self._ensure_browser_installed()

        # 🔍 LOG DETALHADO para debug
        print(f"🔍 [PLAYWRIGHT DEBUG] Iniciando browser com headless={self.headless}, browser_type={self.browser_type}")

        self.playwright = sync_playwright().start()

        browser_launcher = getattr(self.playwright, self.browser_type)
        self.browser = browser_launcher.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-gpu',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--start-maximized',  # ✅ Maximizar janela
                '--window-size=1920,1080'  # ✅ Tamanho inicial grande
            ]
        )

        # ✅ Usar no_viewport para permitir maximização completa
        # (viewport fixo impede que a janela maximize corretamente)
        self.context = self.browser.new_context(
            no_viewport=True,  # ✅ Permite janela maximizada real
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='pt-BR',
            timezone_id='America/Sao_Paulo',
            geolocation={'latitude': -23.5505, 'longitude': -46.6333},
            permissions=['geolocation'],
            extra_http_headers={
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            }
        )

        self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        self.page = self.context.new_page()

    def stop(self):
        """Fecha Playwright"""
        try:
            if self.page:
                self.page.close()
        except:
            pass

        try:
            if self.context:
                self.context.close()
        except:
            pass

        try:
            if self.browser:
                self.browser.close()
        except:
            pass

        try:
            if self.playwright:
                self.playwright.stop()
        except:
            pass

    def get_page(self) -> Page:
        """Retorna página atual"""
        return self.page

    def new_page(self) -> Page:
        """Cria nova página no mesmo contexto"""
        if self.context:
            return self.context.new_page()
        return None

    def __enter__(self):
        """Context manager support"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup"""
        self.stop()
