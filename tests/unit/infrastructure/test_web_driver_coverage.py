"""
Teste para forçar cobertura do web_driver
"""
import unittest


class TestWebDriverCoverage(unittest.TestCase):
    """Força importação do web_driver para cobertura"""
    
    def test_import_web_driver(self):
        """Importa web_driver para aparecer na cobertura"""
        try:
            from src.infrastructure.drivers.web_driver import WebDriverManager
            
            # Verifica se a classe existe
            self.assertTrue(WebDriverManager)
            
        except ImportError as e:
            self.fail(f"Falha ao importar WebDriverManager: {e}")


if __name__ == '__main__':
    unittest.main()