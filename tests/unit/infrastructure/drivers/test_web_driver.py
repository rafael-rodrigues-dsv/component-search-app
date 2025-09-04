"""
Testes completos para WebDriverManager
"""
import unittest
from unittest.mock import patch, MagicMock, Mock
import sys
import os

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src.infrastructure.drivers.web_driver import WebDriverManager


class TestWebDriverManager(unittest.TestCase):
    """Testes completos para WebDriverManager"""

    def setUp(self):
        self.driver_path = "test/chromedriver.exe"
        self.manager = WebDriverManager(self.driver_path)

    def test_init_with_default_path(self):
        """Testa inicialização com caminho padrão"""
        manager = WebDriverManager()
        self.assertEqual(manager.driver_path, "drivers/chromedriver.exe")
        self.assertIsNone(manager.driver)
        self.assertIsNone(manager.wait)

    def test_init_with_custom_path(self):
        """Testa inicialização com caminho customizado"""
        custom_path = "custom/path/chromedriver.exe"
        manager = WebDriverManager(custom_path)
        self.assertEqual(manager.driver_path, custom_path)

    @patch('src.infrastructure.drivers.web_driver.webdriver.Chrome')
    @patch('src.infrastructure.drivers.web_driver.Service')
    @patch('src.infrastructure.drivers.web_driver.Options')
    @patch('src.infrastructure.drivers.web_driver.WebDriverWait')
    @patch('random.choice')
    @patch('random.randint')
    @patch('time.sleep')
    def test_start_driver_success(self, mock_sleep, mock_randint, mock_choice, mock_wait, mock_options, mock_service, mock_chrome):
        """Testa inicialização bem-sucedida do driver com anti-detecção"""
        # Setup mocks
        mock_driver = MagicMock()
        mock_chrome.return_value = mock_driver
        mock_wait_instance = MagicMock()
        mock_wait.return_value = mock_wait_instance
        
        # Mock para seleções aleatórias
        mock_choice.side_effect = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",  # user agent
            (1920, 1080)  # resolution
        ]
        mock_randint.side_effect = [50, 50]  # window position

        # Execute
        result = self.manager.start_driver()

        # Verify
        self.assertTrue(result)
        self.assertEqual(self.manager.driver, mock_driver)
        self.assertEqual(self.manager.wait, mock_wait_instance)

        # Verifica se configurações foram aplicadas
        mock_options.assert_called_once()
        mock_service.assert_called_once_with(self.driver_path)
        mock_chrome.assert_called_once()
        
        # Verifica se script stealth foi executado
        mock_driver.execute_script.assert_called()

    @patch('src.infrastructure.drivers.web_driver.webdriver.Chrome')
    @patch('src.infrastructure.drivers.web_driver.Service')
    def test_start_driver_failure(self, mock_service, mock_chrome):
        """Testa falha na inicialização do driver"""
        # Setup mock para lançar exceção
        mock_chrome.side_effect = Exception("WebDriver failed")

        # Execute - deve capturar WebDriverException e retornar False
        with patch('src.infrastructure.drivers.web_driver.WebDriverException', Exception):
            result = self.manager.start_driver()

            # Verify
            self.assertFalse(result)
            self.assertIsNone(self.manager.driver)

    def test_navigate_to_success(self):
        """Testa navegação bem-sucedida"""
        # Setup mock driver
        mock_driver = MagicMock()
        self.manager.driver = mock_driver

        # Execute
        result = self.manager.navigate_to("https://example.com")

        # Verify
        self.assertTrue(result)
        mock_driver.get.assert_called_once_with("https://example.com")

    def test_navigate_to_failure(self):
        """Testa falha na navegação"""
        # Setup mock driver que lança exceção
        mock_driver = MagicMock()
        self.manager.driver = mock_driver

        # Simula WebDriverException
        from selenium.common.exceptions import WebDriverException
        mock_driver.get.side_effect = WebDriverException("Navigation failed")

        # Execute
        result = self.manager.navigate_to("https://example.com")

        # Verify
        self.assertFalse(result)

    @patch('src.infrastructure.drivers.web_driver.webdriver.Chrome')
    @patch('src.infrastructure.drivers.web_driver.Service')
    def test_start_driver_webdriver_exception(self, mock_service, mock_chrome):
        """Testa tratamento de WebDriverException no start_driver"""
        from selenium.common.exceptions import WebDriverException
        mock_chrome.side_effect = WebDriverException("Chrome failed")

        # Execute
        result = self.manager.start_driver()

        # Verify
        self.assertFalse(result)
        self.assertIsNone(self.manager.driver)

    def test_close_driver_with_driver(self):
        """Testa fechamento do driver quando existe"""
        # Setup mock driver
        mock_driver = MagicMock()
        self.manager.driver = mock_driver

        # Execute
        self.manager.close_driver()

        # Verify
        mock_driver.quit.assert_called_once()
        self.assertIsNone(self.manager.driver)

    def test_close_driver_without_driver(self):
        """Testa fechamento quando não há driver"""
        # Execute sem driver
        self.manager.close_driver()

        # Verify - não deve lançar exceção
        self.assertIsNone(self.manager.driver)
    
    @patch('os.path.exists')
    def test_get_browser_path_brave_found(self, mock_exists):
        """Testa obtenção do caminho do Brave"""
        mock_exists.side_effect = [True, False]  # Primeiro caminho existe
        manager = WebDriverManager(browser="brave")
        
        path = manager._get_browser_path()
        self.assertEqual(path, "C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe")
    
    @patch('os.path.exists')
    def test_get_browser_path_brave_not_found(self, mock_exists):
        """Testa quando Brave não é encontrado"""
        mock_exists.return_value = False
        manager = WebDriverManager(browser="brave")
        
        path = manager._get_browser_path()
        self.assertIsNone(path)
    
    def test_get_browser_path_chrome(self):
        """Testa obtenção do caminho do Chrome (padrão)"""
        manager = WebDriverManager(browser="chrome")
        
        path = manager._get_browser_path()
        self.assertIsNone(path)  # Chrome usa caminho padrão


if __name__ == '__main__':
    unittest.main()
