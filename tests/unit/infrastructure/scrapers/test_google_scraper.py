"""
Testes otimizados para GoogleScraper - Versão Rápida
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

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
        # Mock HumanBehaviorSimulator
        cls.scraper.human_behavior = MagicMock()
        cls.scraper.searches_count = 0

    def setUp(self):
        self.mock_driver.reset_mock()
        # Reset PropertyMock side effects
        from unittest.mock import PropertyMock
        type(self.mock_driver).title = PropertyMock(return_value="Test Company")
        type(self.mock_driver).page_source = PropertyMock(return_value="Test page")

    def test_core_functionality(self, mock_sleep, mock_wait, mock_uniform, mock_time_sleep):
        """Testa funcionalidades principais em lote"""
        # Mock search box for human navigation
        mock_search_box = MagicMock()
        mock_wait.return_value.until.return_value = mock_search_box

        # Search success with human behavior
        self.mock_driver.page_source = "normal search results"
        self.assertTrue(self.scraper.search("test"))

        # Verify human behavior was called
        self.scraper.human_behavior.typing_delay.assert_called()
        self.scraper.human_behavior.random_delay.assert_called()

        # Search failure
        self.mock_driver.get.side_effect = Exception("Error")
        self.assertFalse(self.scraper.search("test"))
        self.mock_driver.get.side_effect = None

        # Get links with human behavior
        mock_link = MagicMock()
        mock_link.get_attribute.return_value = "https://example.com"
        self.mock_driver.find_elements.return_value = [mock_link]

        # Mock human behavior for scroll and mouse
        self.scraper.human_behavior.scroll_behavior = MagicMock()
        self.scraper.human_behavior.mouse_movement = MagicMock()

        links = self.scraper.get_result_links(["blacklist.com"])
        self.assertIn("https://example.com", links)

        # Verify human behavior was called
        self.scraper.human_behavior.scroll_behavior.assert_called_with(self.mock_driver)

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

        # Mock human behavior methods
        self.scraper.human_behavior.reading_delay.return_value = 0.1
        self.scraper.human_behavior.scroll_behavior = MagicMock()
        self.scraper.human_behavior.mouse_movement = MagicMock()

        # Extract company data
        result = self.scraper.extract_company_data("https://example.com", 5)
        self.assertIsInstance(result, CompanyModel)
        self.assertEqual(result.url, "https://example.com")

        # Verify human behavior was used
        self.scraper.human_behavior.scroll_behavior.assert_called()
        self.scraper.human_behavior.reading_delay.assert_called()

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
        # Test CAPTCHA detection
        self.mock_driver.page_source = "unusual traffic detected captcha"
        mock_search_box = MagicMock()
        mock_wait.return_value.until.return_value = mock_search_box
        result = self.scraper.search("test")
        self.assertTrue(result)  # Should use fallback

        # Test session break behavior
        self.scraper.human_behavior.session_break_needed.return_value = True
        self.scraper.human_behavior.take_session_break = MagicMock()
        self.scraper.search("test")
        self.scraper.human_behavior.take_session_break.assert_called()

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

        # Reset human behavior mocks
        self.scraper.human_behavior.reading_delay.return_value = 0.1
        self.scraper.human_behavior.scroll_behavior = MagicMock()
        self.scraper.human_behavior.mouse_movement = MagicMock()

        result = self.scraper.extract_company_data("https://example.com", 5)
        # Com título com exceção, name fica vazio e domain é extraído da URL
        self.assertEqual(result.name, "")
        self.assertEqual(result.domain, "example.com")

        # Test interactive search failure fallback
        mock_wait.return_value.until.side_effect = Exception("Search box not found")
        self.mock_driver.page_source = "normal page"
        result = self.scraper.search("test")
        self.assertTrue(result)  # Should fallback to direct URL


if __name__ == '__main__':
    unittest.main()
