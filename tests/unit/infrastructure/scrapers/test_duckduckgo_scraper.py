"""
Testes otimizados para DuckDuckGoScraper - Versão Rápida
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src.infrastructure.scrapers.duckduckgo_scraper import DuckDuckGoScraper
from src.domain.models.company_model import CompanyModel

# Mocks globais para máxima velocidade
@patch('time.sleep', return_value=None)
@patch('random.uniform', return_value=0.01)
@patch('src.infrastructure.scrapers.duckduckgo_scraper.WebDriverWait')
@patch('src.infrastructure.scrapers.duckduckgo_scraper.time.sleep', return_value=None)
class TestDuckDuckGoScraperFast(unittest.TestCase):
    """Testes rápidos para DuckDuckGoScraper"""
    
    @classmethod
    def setUpClass(cls):
        cls.mock_driver_manager = MagicMock()
        cls.mock_driver = MagicMock()
        cls.mock_driver_manager.driver = cls.mock_driver
        cls.scraper = DuckDuckGoScraper(cls.mock_driver_manager)
    
    def setUp(self):
        self.mock_driver.reset_mock()
        # Reset PropertyMock side effects
        from unittest.mock import PropertyMock
        type(self.mock_driver).title = PropertyMock(return_value="Test Company")
        type(self.mock_driver).page_source = PropertyMock(return_value="Test page")
    
    def test_core_functionality(self, mock_sleep, mock_wait, mock_uniform, mock_time_sleep):
        """Testa funcionalidades principais em lote"""
        # Search success
        mock_element = MagicMock()
        mock_wait.return_value.until.return_value = mock_element
        self.assertTrue(self.scraper.search("test"))
        self.mock_driver.get.assert_called_with("https://duckduckgo.com/")
        
        # Search failure
        self.mock_driver.get.side_effect = Exception("Error")
        self.assertFalse(self.scraper.search("test"))
        self.mock_driver.get.side_effect = None
        
        # Get links
        mock_card = MagicMock()
        mock_link = MagicMock()
        mock_link.get_attribute.return_value = "https://example.com"
        mock_card.find_elements.return_value = [mock_link]
        self.mock_driver.find_elements.return_value = [mock_card]
        links = self.scraper.get_result_links(["blacklist.com"])
        self.assertIn("https://example.com", links)
        
        # Next page
        mock_button = MagicMock()
        mock_button.is_displayed.return_value = True
        self.mock_driver.find_element.return_value = mock_button
        self.assertTrue(self.scraper.go_to_next_page())
    
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
        
        # Extract emails
        emails = self.scraper._extract_emails_fast()
        self.assertIsInstance(emails, list)
        
        # Extract phones
        phones = self.scraper._extract_phones_fast()
        self.assertIsInstance(phones, list)
        
        # Get company name
        name = self.scraper._get_company_name_fast("https://example.com")
        self.assertEqual(name, "Test Company")
    
    def test_validation_and_edge_cases(self, mock_sleep, mock_wait, mock_uniform, mock_time_sleep):
        """Testa validações e casos extremos em lote"""
        # Blacklist validation
        self.assertTrue(self.scraper._is_blacklisted("https://blacklist.com", ["blacklist.com"]))
        self.assertFalse(self.scraper._is_blacklisted("https://example.com", ["blacklist.com"]))
        
        # Exception handling
        self.mock_driver.execute_script.side_effect = Exception("Error")
        result = self.scraper.extract_company_data("https://example.com", 5)
        self.assertIsInstance(result, CompanyModel)
        self.assertEqual(result.name, "")
        self.mock_driver.execute_script.side_effect = None
        
        # Empty title fallback
        from unittest.mock import PropertyMock
        type(self.mock_driver).title = PropertyMock(return_value="")
        name = self.scraper._get_company_name_fast("https://example.com")
        self.assertEqual(name, "example.com")
        # Reset title
        type(self.mock_driver).title = PropertyMock(return_value="Test Company")
        
        # Go to next page without button - fallback to scroll
        self.mock_driver.find_element.side_effect = Exception("No button")
        result = self.scraper.go_to_next_page()
        self.assertTrue(result)
        self.mock_driver.find_element.side_effect = None
        
        # Exception in get_result_links
        self.mock_driver.execute_script.side_effect = Exception("Script error")
        links = self.scraper.get_result_links(["blacklist.com"])
        self.assertEqual(links, [])
        self.mock_driver.execute_script.side_effect = None
        
        # Exception in _extract_emails_fast
        from unittest.mock import PropertyMock
        type(self.mock_driver).page_source = PropertyMock(side_effect=Exception("Page error"))
        emails = self.scraper._extract_emails_fast()
        self.assertEqual(emails, [])
        
        # Exception in _extract_phones_fast
        phones = self.scraper._extract_phones_fast()
        self.assertEqual(phones, [])
        
        # Exception in _get_company_name_fast
        type(self.mock_driver).title = PropertyMock(side_effect=Exception("Title error"))
        name = self.scraper._get_company_name_fast("https://example.com")
        self.assertEqual(name, "example.com")
        # Reset title mock
        type(self.mock_driver).title = PropertyMock(return_value="Test Company")


    def test_additional_coverage(self, mock_sleep, mock_wait, mock_uniform, mock_time_sleep):
        """Testa linhas adicionais para 100% cobertura"""
        # Test finally block exception in extract_company_data
        self.mock_driver.page_source = "test"
        self.mock_driver.title = "Test"
        self.mock_driver.window_handles = ["tab1", "tab2"]
        self.mock_driver.close.side_effect = Exception("Close error")
        result = self.scraper.extract_company_data("https://example.com", 5)
        self.assertIsInstance(result, CompanyModel)
        self.mock_driver.close.side_effect = None
        
        # Test go_to_next_page general exception
        self.mock_driver.execute_script.side_effect = Exception("General error")
        result = self.scraper.go_to_next_page()
        self.assertFalse(result)
        self.mock_driver.execute_script.side_effect = None
        
        # Test extract with limits and breaks
        self.mock_driver.page_source = "email1@test.com email2@test.com email3@test.com email4@test.com email5@test.com email6@test.com"
        emails = self.scraper._extract_emails_fast()
        self.assertLessEqual(len(emails), 5)
        
        # Test phones with limits
        self.mock_driver.page_source = "(11) 98765-4321 (21) 98765-4321 (31) 98765-4321 (41) 98765-4321"
        phones = self.scraper._extract_phones_fast()
        self.assertLessEqual(len(phones), 3)


if __name__ == '__main__':
    unittest.main()