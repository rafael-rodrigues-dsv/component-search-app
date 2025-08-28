"""
Camada de Infraestrutura - Gerenciamento do WebDriver
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException


class WebDriverManager:
    """Gerenciador do WebDriver Chrome"""
    
    def __init__(self, driver_path: str = "drivers/chromedriver.exe"):
        self.driver_path = driver_path
        self.driver = None
        self.wait = None
    
    def start_driver(self) -> bool:
        """Inicia o driver Chrome com anti-detecção"""
        try:
            options = Options()
            
            # Anti-detecção avançada
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Stealth avançado
            options.add_argument("--disable-extensions-file-access-check")
            options.add_argument("--disable-extensions-http-throttling")
            options.add_argument("--disable-ipc-flooding-protection")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-features=TranslateUI")
            options.add_argument("--disable-component-extensions-with-background-pages")
            
            # User-Agent rotativo
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
            import random
            selected_ua = random.choice(user_agents)
            options.add_argument(f"--user-agent={selected_ua}")
            
            # Configurações de janela com resoluções comuns
            resolutions = [(1920, 1080), (1366, 768), (1536, 864), (1440, 900), (1280, 720)]
            width, height = random.choice(resolutions)
            options.add_argument(f"--window-size={width},{height}")
            
            # Preferências para parecer mais humano
            prefs = {
                "profile.default_content_setting_values": {
                    "notifications": 2,
                    "geolocation": 2,
                },
                "profile.managed_default_content_settings": {
                    "images": 1
                }
            }
            options.add_experimental_option("prefs", prefs)
            
            # Outras configurações
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--log-level=3")
            options.add_argument("--disable-logging")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")
            
            print("[INFO] Executando com navegador visível")
            
            service = Service(self.driver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Script stealth completo
            stealth_script = """
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['pt-BR', 'pt', 'en']});
            window.chrome = {runtime: {}};
            Object.defineProperty(navigator, 'permissions', {get: () => ({query: () => Promise.resolve({state: 'granted'})})});
            """
            self.driver.execute_script(stealth_script)
            
            self.wait = WebDriverWait(self.driver, 10)
            
            return True
        except WebDriverException:
            return False
    
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