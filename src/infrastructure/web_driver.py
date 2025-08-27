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
    
    def __init__(self, driver_path: str = "chromedriver.exe"):
        self.driver_path = driver_path
        self.driver = None
        self.wait = None
    
    def start_driver(self) -> bool:
        """Inicia o driver Chrome"""
        try:
            options = Options()
            options.add_argument("--window-size=1200,800")
            options.add_argument("--disable-notifications")
            options.add_argument("--disable-popup-blocking")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            
            print("[INFO] Executando com navegador visível")
            
            service = Service(self.driver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
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