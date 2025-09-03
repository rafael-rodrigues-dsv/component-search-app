"""
Testes otimizados para GoogleScraper - Versão Rápida
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src.infrastructure.scrapers.google_scraper import GoogleScraper
from src.domain.models.company_model import CompanyModel


# Mocks globais para máxima velocidade
@patch('time.sleep', return_value=None)
@patch('random.uniform', return_value=0.01)
@patch('src.infrastructure.scrapers.google_scraper.WebDriverWait')
@patch('src.infrastructure.scrapers.google_scraper.time.sleep', return_value=None)
class TestGoogleScraperFast(unittest.TestCase):
    """Testes rápidos para GoogleScraper"""

    @classmethod
    def setUpClass(cls):
        cls.mock_driver = MagicMock()
        cls.scraper = GoogleScraper(cls.mock_driver)

    def setUp(self):
        self.mock_driver.reset_mock()
        # Reset PropertyMock side effects
        from unittest.mock import PropertyMock
        type(self.mock_driver).title = PropertyMock(return_value="Test Company")
        type(self.mock_driver).page_source = PropertyMock(return_value="Test page")

    def test_core_functionality(self, mock_sleep, mock_wait, mock_uniform, mock_time_sleep):
        """Testa funcionalidades principais em lote"""
        # Search success
        mock_wait.return_value.until.return_value = MagicMock()
        self.assertTrue(self.scraper.search("test"))

        # Search failure
        self.mock_driver.get.side_effect = Exception("Error")
        self.assertFalse(self.scraper.search("test"))
        self.mock_driver.get.side_effect = None

        # Get links
        mock_link = MagicMock()
        mock_link.get_attribute.return_value = "https://example.com"
        self.mock_driver.find_elements.return_value = [mock_link]
        links = self.scraper.get_result_links(["blacklist.com"])
        self.assertIn("https://example.com", links)

        # Next page
        self.mock_driver.current_url = "https://google.com/search?q=test"
        self.scraper.go_to_next_page()
        self.mock_driver.get.assert_called()

    def test_data_extraction(self, mock_sleep, mock_wait, mock_uniform, mock_time_sleep):
        """Testa extração de dados em lote"""
        # Setup
        self.mock_driver.page_source = "Contact: test@example.com (11) 99999-8888"
        self.mock_driver.title = "Test Company"
        self.mock_driver.window_handles = ["tab1", "tab2"]

        # Extract company data
        result = self.scraper.extract_company_data("https://example.com", 5)
        self.assertIsInstance(result, CompanyModel)
        self.assertEqual(result.url, "https://example.com")

        # Extract phones
        phones = self.scraper._extract_phones_fast("(11) 98765-4321 (21) 98765-4321")
        self.assertLessEqual(len(phones), 3)

    def test_validation_and_edge_cases(self, mock_sleep, mock_wait, mock_uniform, mock_time_sleep):
        """Testa validações e casos extremos em lote"""
        # URL validation
        self.assertTrue(self.scraper._is_valid_url("https://example.com"))
        self.assertFalse(self.scraper._is_valid_url("invalid"))
        self.assertFalse(self.scraper._is_valid_url("https://google.com"))
        self.assertFalse(self.scraper._is_valid_url(None))
        self.assertFalse(self.scraper._is_valid_url(""))

        # Exception handling
        self.mock_driver.execute_script.side_effect = Exception("Error")
        result = self.scraper.extract_company_data("https://example.com", 5)
        self.assertIsInstance(result, CompanyModel)
        self.assertEqual(result.name, "")
        self.mock_driver.execute_script.side_effect = None

        # Fallback scenarios
        mock_wait.return_value.until.side_effect = Exception("Wait failed")
        self.assertTrue(self.scraper.search("test"))  # Should use fallback
        mock_wait.return_value.until.side_effect = None

        # Go to next page edge cases
        self.mock_driver.current_url = "https://google.com/search?q=test&start=10"
        mock_wait.return_value.until.side_effect = Exception("Wait failed")
        self.assertFalse(self.scraper.go_to_next_page())
        mock_wait.return_value.until.side_effect = None

        # Extract phones with exception
        with patch('re.findall', side_effect=Exception("Regex error")):
            phones = self.scraper._extract_phones_fast("test")
            self.assertEqual(phones, [])

    def test_additional_coverage(self, mock_sleep, mock_wait, mock_uniform, mock_time_sleep):
        """Testa linhas adicionais para 100% cobertura"""
        # Test fallback search failure
        self.mock_driver.get.side_effect = Exception("Driver error")
        result = self.scraper._fallback_search_simple("test")
        self.assertFalse(result)
        self.mock_driver.get.side_effect = None

        # Test extract with empty selectors
        self.mock_driver.find_elements.return_value = []
        links = self.scraper.get_result_links(["blacklist.com"])
        self.assertEqual(links, [])

        # Test extract with exception in link processing
        mock_link = MagicMock()
        mock_link.get_attribute.side_effect = Exception("Attribute error")
        self.mock_driver.find_elements.return_value = [mock_link]
        links = self.scraper.get_result_links(["blacklist.com"])
        self.assertEqual(links, [])

        # Test go_to_next_page with regex edge case
        self.mock_driver.current_url = "https://google.com/search?q=test&start="
        self.scraper.go_to_next_page()

        # Test extract_company_data with title exception
        from unittest.mock import PropertyMock
        type(self.mock_driver).title = PropertyMock(side_effect=Exception("Title error"))
        self.mock_driver.page_source = "test"
        self.mock_driver.window_handles = ["tab1", "tab2"]
        result = self.scraper.extract_company_data("https://example.com", 5)
        self.assertEqual(result.name, "example.com")


if __name__ == '__main__':
    unittest.main()
