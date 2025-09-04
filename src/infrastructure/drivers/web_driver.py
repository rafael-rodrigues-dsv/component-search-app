"""
Camada de Infraestrutura - Gerenciamento do WebDriver
"""
from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait

from ..network.retry_manager import RetryManager


class WebDriverManager:
    """Gerenciador do WebDriver Chrome/Brave"""

    def __init__(self, driver_path: str = "drivers/chromedriver.exe", browser: str = "chrome"):
        self.driver_path = driver_path
        self.browser = browser
        self.driver = None
        self.wait = None

    def _get_browser_path(self) -> str:
        """Obtém caminho do navegador baseado no tipo"""
        import os

        if self.browser == "brave":
            brave_paths = [
                "C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe",
                "C:/Program Files (x86)/BraveSoftware/Brave-Browser/Application/brave.exe"
            ]
            for path in brave_paths:
                if os.path.exists(path):
                    return path

        return None  # Chrome usa caminho padrão

    def start_driver(self) -> bool:
        """Inicia o driver Chrome com anti-detecção avançada"""
        try:
            options = Options()
            import random
            import time

            # === ANTI-DETECÇÃO CRÍTICA ===
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            options.add_experimental_option('useAutomationExtension', False)

            # Novos argumentos anti-detecção
            options.add_argument("--disable-features=VizDisplayCompositor")
            options.add_argument("--disable-features=TranslateUI,BlinkGenPropertyTrees")
            options.add_argument("--disable-default-apps")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-plugins-discovery")
            options.add_argument("--disable-preconnect")
            options.add_argument("--disable-sync")
            options.add_argument("--disable-translate")

            # Headers mais realistas
            options.add_argument("--accept-lang=pt-BR,pt;q=0.9,en;q=0.8")
            options.add_argument("--accept-encoding=gzip, deflate, br")

            # === USER-AGENT MAIS REALISTA ===
            realistic_uas = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            ]
            selected_ua = random.choice(realistic_uas)
            options.add_argument(f"--user-agent={selected_ua}")

            # === RESOLUÇÃO E VIEWPORT REALISTAS ===
            common_resolutions = [
                (1920, 1080), (1366, 768), (1536, 864), (1440, 900),
                (1280, 720), (1600, 900), (1024, 768)
            ]
            width, height = random.choice(common_resolutions)
            options.add_argument(f"--window-size={width},{height}")

            # Posição aleatória da janela
            x_pos = random.randint(0, 100)
            y_pos = random.randint(0, 100)
            options.add_argument(f"--window-position={x_pos},{y_pos}")

            # === PREFERÊNCIAS REALISTAS ===
            prefs = {
                "profile.default_content_setting_values": {
                    "notifications": 2,
                    "geolocation": 1,  # Permitir geolocalização
                    "media_stream": 2,
                },
                "profile.managed_default_content_settings": {
                    "images": 1
                },
                "profile.default_content_settings": {
                    "popups": 0
                },
                # Simular histórico de navegação
                "profile.content_settings.exceptions.automatic_downloads": {
                    "[*.]google.com,*": {"setting": 1}
                },
                # Idioma
                "intl.accept_languages": "pt-BR,pt,en-US,en"
            }
            options.add_experimental_option("prefs", prefs)

            # === CONFIGURAÇÕES DE PERFORMANCE ===
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--log-level=3")
            options.add_argument("--disable-logging")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")

            # === PROXY ROTATION (se disponível) ===
            try:
                from ..network.proxy_manager import ProxyManager
                proxy_manager = ProxyManager()
                working_proxies = proxy_manager.get_working_proxies()
                if working_proxies:
                    proxy = random.choice(working_proxies)
                    options.add_argument(f"--proxy-server=http://{proxy}")
                    print(f"[INFO] Usando proxy: {proxy}")
            except Exception as e:
                print(f"[DEBUG] Proxy não disponível: {str(e)[:30]}")

            # Configurar navegador específico
            browser_path = self._get_browser_path()
            if browser_path:
                options.binary_location = browser_path
                print(f"[INFO] Executando com {self.browser.title()} Browser visível")
            else:
                print("[INFO] Executando com navegador visível")

            service = Service(self.driver_path)
            self.driver = webdriver.Chrome(service=service, options=options)

            # === SCRIPT STEALTH AVANÇADO ===
            stealth_script = """
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            
            // Mock plugins realistas
            Object.defineProperty(navigator, 'plugins', {
                get: () => {
                    return [
                        {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer'},
                        {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai'},
                        {name: 'Native Client', filename: 'internal-nacl-plugin'}
                    ];
                }
            });
            
            // Languages realistas
            Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt', 'en-US', 'en']});
            
            // Chrome runtime
            window.chrome = {
                runtime: {
                    onConnect: undefined,
                    onMessage: undefined
                }
            };
            
            // Permissions API
            Object.defineProperty(navigator, 'permissions', {
                get: () => ({
                    query: () => Promise.resolve({state: 'granted'})
                })
            });
            
            // Hardware concurrency realista
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 4});
            
            // Device memory
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
            
            // Connection
            Object.defineProperty(navigator, 'connection', {
                get: () => ({
                    effectiveType: '4g',
                    rtt: 50,
                    downlink: 10
                })
            });
            
            // Remove automation indicators
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            """
            self.driver.execute_script(stealth_script)

            # Simular comportamento humano inicial
            time.sleep(random.uniform(1.0, 3.0))

            # Movimento de mouse aleatório
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(self.driver)
                actions.move_by_offset(random.randint(10, 100), random.randint(10, 100))
                actions.perform()
            except Exception:
                pass

            self.wait = WebDriverWait(self.driver, 10)

            return True
        except WebDriverException:
            return False

    @RetryManager.with_retry(max_attempts=3, base_delay=1.5, exceptions=(WebDriverException,))
    def navigate_to(self, url: str) -> bool:
        """Navega para URL"""
        try:
            self.driver.get(url)
            return True
        except WebDriverException:
            return False

    def close_driver(self):
        """Fecha o driver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
