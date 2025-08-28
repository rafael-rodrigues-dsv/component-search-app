"""
Testes unitários para ChromeDriverManager
"""
import unittest
import sys
import os
from unittest.mock import patch, mock_open, MagicMock
import zipfile

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src.infrastructure.drivers.chromedriver_manager import ChromeDriverManager


class TestChromeDriverManager(unittest.TestCase):
    """Testes para ChromeDriverManager"""
    
    @patch('os.path.exists')
    def test_ensure_chromedriver_already_exists(self, mock_exists):
        """Testa quando ChromeDriver já existe"""
        mock_exists.return_value = True
        
        result = ChromeDriverManager.ensure_chromedriver()
        
        self.assertTrue(result)
        mock_exists.assert_called_once_with("drivers/chromedriver.exe")
    
    @patch('os.path.exists')
    @patch.object(ChromeDriverManager, '_get_chrome_version')
    @patch.object(ChromeDriverManager, '_get_download_url')
    @patch.object(ChromeDriverManager, '_download_and_install')
    def test_ensure_chromedriver_download_success(self, mock_download, mock_get_url, mock_get_version, mock_exists):
        """Testa download bem-sucedido do ChromeDriver"""
        mock_exists.return_value = False
        mock_get_version.return_value = "119"
        mock_get_url.return_value = "https://test.com/chromedriver.zip"
        mock_download.return_value = True
        
        result = ChromeDriverManager.ensure_chromedriver()
        
        self.assertTrue(result)
        mock_get_version.assert_called_once()
        mock_get_url.assert_called_once_with("119")
        mock_download.assert_called_once_with("https://test.com/chromedriver.zip")
    
    @patch('os.path.exists')
    @patch.object(ChromeDriverManager, '_get_chrome_version')
    @patch.object(ChromeDriverManager, '_get_download_url')
    def test_ensure_chromedriver_no_download_url(self, mock_get_url, mock_get_version, mock_exists):
        """Testa quando não encontra URL de download"""
        mock_exists.return_value = False
        mock_get_version.return_value = "119"
        mock_get_url.return_value = None
        
        result = ChromeDriverManager.ensure_chromedriver()
        
        self.assertFalse(result)
    
    @patch('os.path.exists')
    @patch.object(ChromeDriverManager, '_get_chrome_version')
    def test_ensure_chromedriver_exception(self, mock_get_version, mock_exists):
        """Testa tratamento de exceção"""
        mock_exists.return_value = False
        mock_get_version.side_effect = Exception("Erro teste")
        
        result = ChromeDriverManager.ensure_chromedriver()
        
        self.assertFalse(result)
    
    @patch('winreg.OpenKey')
    @patch('winreg.QueryValueEx')
    def test_get_chrome_version_success(self, mock_query, mock_open):
        """Testa detecção bem-sucedida da versão do Chrome"""
        mock_query.return_value = ("119.0.6045.105", None)
        
        version = ChromeDriverManager._get_chrome_version()
        
        self.assertEqual(version, "119")
    
    @patch('winreg.OpenKey')
    def test_get_chrome_version_exception(self, mock_open):
        """Testa versão padrão quando há exceção"""
        mock_open.side_effect = Exception("Registry error")
        
        version = ChromeDriverManager._get_chrome_version()
        
        self.assertEqual(version, "119")
    
    @patch('requests.get')
    def test_get_download_url_success(self, mock_get):
        """Testa busca bem-sucedida de URL de download"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'versions': [
                {
                    'version': '119.0.6045.105',
                    'downloads': {
                        'chromedriver': [
                            {
                                'platform': 'win64',
                                'url': 'https://test.com/chromedriver-win64.zip'
                            }
                        ]
                    }
                }
            ]
        }
        mock_get.return_value = mock_response
        
        url = ChromeDriverManager._get_download_url("119")
        
        self.assertEqual(url, 'https://test.com/chromedriver-win64.zip')
    
    @patch('requests.get')
    def test_get_download_url_no_match(self, mock_get):
        """Testa quando não encontra versão compatível"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'versions': [
                {
                    'version': '118.0.5993.70',
                    'downloads': {
                        'chromedriver': [
                            {
                                'platform': 'win64',
                                'url': 'https://test.com/chromedriver-win64.zip'
                            }
                        ]
                    }
                }
            ]
        }
        mock_get.return_value = mock_response
        
        url = ChromeDriverManager._get_download_url("119")
        
        self.assertIsNone(url)
    
    @patch('requests.get')
    def test_get_download_url_no_win64_platform(self, mock_get):
        """Testa quando não encontra plataforma win64"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'versions': [
                {
                    'version': '119.0.6045.105',
                    'downloads': {
                        'chromedriver': [
                            {
                                'platform': 'linux64',
                                'url': 'https://test.com/chromedriver-linux64.zip'
                            }
                        ]
                    }
                }
            ]
        }
        mock_get.return_value = mock_response
        
        url = ChromeDriverManager._get_download_url("119")
        
        self.assertIsNone(url)
    
    @patch('requests.get')
    @patch('builtins.open', new_callable=mock_open)
    @patch('zipfile.ZipFile')
    @patch('os.makedirs')
    @patch('os.remove')
    def test_download_and_install_success(self, mock_remove, mock_makedirs, mock_zipfile, mock_file, mock_get):
        """Testa download e instalação bem-sucedidos"""
        # Mock da resposta HTTP
        mock_response = MagicMock()
        mock_response.content = b"fake zip content"
        mock_get.return_value = mock_response
        
        # Mock do arquivo ZIP
        mock_zip_instance = MagicMock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
        
        # Mock do arquivo chromedriver.exe dentro do ZIP
        mock_file_info = MagicMock()
        mock_file_info.filename = 'chromedriver-win64/chromedriver.exe'
        mock_zip_instance.filelist = [mock_file_info]
        
        mock_source_file = MagicMock()
        mock_source_file.read.return_value = b"fake chromedriver content"
        mock_zip_instance.open.return_value = mock_source_file
        
        result = ChromeDriverManager._download_and_install("https://test.com/chromedriver.zip")
        
        self.assertTrue(result)
        mock_get.assert_called_once_with("https://test.com/chromedriver.zip", timeout=30)
        mock_makedirs.assert_called_once_with('drivers', exist_ok=True)
        mock_remove.assert_called_once_with("chromedriver.zip")
    
    @patch('requests.get')
    def test_download_and_install_request_exception(self, mock_get):
        """Testa exceção durante download"""
        mock_get.side_effect = Exception("Network error")
        
        with self.assertRaises(Exception):
            ChromeDriverManager._download_and_install("https://test.com/chromedriver.zip")


if __name__ == '__main__':
    unittest.main()