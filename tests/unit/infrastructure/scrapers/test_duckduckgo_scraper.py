"""
Testes completos para DuckDuckGoScraper
"""
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import sys
import os

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src.infrastructure.scrapers.duckduckgo_scraper import DuckDuckGoScraper
from src.domain.models.company_model import CompanyModel


class TestDuckDuckGoScraper(unittest.TestCase):
    """Testes para DuckDuckGoScraper"""
    
    def setUp(self):
        self.mock_driver_manager = MagicMock()
        self.mock_driver = MagicMock()
        self.mock_driver_manager.driver = self.mock_driver
        self.scraper = DuckDuckGoScraper(self.mock_driver_manager)
    
    @patch('src.infrastructure.scrapers.duckduckgo_scraper.WebDriverWait')
    @patch('src.infrastructure.scrapers.duckduckgo_scraper.time.sleep')
    def test_search_success(self, mock_sleep, mock_wait):
        """Testa busca bem-sucedida"""
        # Setup mocks
        mock_element = MagicMock()
        mock_wait.return_value.until.return_value = mock_element
        
        # Execute
        result = self.scraper.search("test query")
        
        # Verify
        self.assertTrue(result)
        self.mock_driver.get.assert_called_with("https://duckduckgo.com/")
    
    def test_search_failure(self):
        """Testa falha na busca"""
        # Setup mock para lançar exceção
        self.mock_driver.get.side_effect = Exception("Search failed")
        
        # Execute
        result = self.scraper.search("test query")
        
        # Verify
        self.assertFalse(result)
    
    def test_get_result_links_success(self):
        """Testa extração de links"""
        # Setup mock elements
        mock_card = MagicMock()
        mock_link = MagicMock()
        mock_link.get_attribute.return_value = "https://example.com"
        mock_card.find_elements.return_value = [mock_link]
        self.mock_driver.find_elements.return_value = [mock_card]
        
        # Execute
        links = self.scraper.get_result_links(["blacklisted.com"])
        
        # Verify
        self.assertIn("https://example.com", links)
    
    def test_get_result_links_blacklisted(self):
        """Testa filtro de blacklist"""
        # Setup mock elements
        mock_card = MagicMock()
        mock_link = MagicMock()
        mock_link.get_attribute.return_value = "https://blacklisted.com/page"
        mock_card.find_elements.return_value = [mock_link]
        self.mock_driver.find_elements.return_value = [mock_card]
        
        # Execute
        links = self.scraper.get_result_links(["blacklisted.com"])
        
        # Verify
        self.assertEqual(len(links), 0)
    
    @patch('src.infrastructure.scrapers.duckduckgo_scraper.WebDriverWait')
    def test_extract_company_data_success(self, mock_wait):
        """Testa extração de dados da empresa"""
        # Setup mocks
        self.mock_driver.page_source = "Contact us at test@example.com or call (11) 99999-8888"
        self.mock_driver.title = "Test Company"
        self.mock_driver.window_handles = ["tab1", "tab2"]
        
        # Execute
        result = self.scraper.extract_company_data("https://example.com", 5)
        
        # Verify
        self.assertIsInstance(result, CompanyModel)
        self.assertEqual(result.url, "https://example.com")
    
    def test_extract_emails_fast(self):
        """Testa extração rápida de e-mails"""
        # Setup mock page source
        self.mock_driver.page_source = "Contact: contato@empresa.com.br, info@site.org, invalid-email"
        
        # Execute
        emails = self.scraper._extract_emails_fast()
        
        # Verify - apenas e-mails válidos devem estar presentes
        self.assertIn("info@site.org", emails)
        self.assertNotIn("invalid-email", emails)
        # Verifica que pelo menos um e-mail foi encontrado
        self.assertGreater(len(emails), 0)
    
    @patch('src.infrastructure.scrapers.duckduckgo_scraper.time.sleep')
    def test_go_to_next_page_success_with_button(self, mock_sleep):
        """Testa navegação para próxima página com botão"""
        # Setup mock button
        mock_button = MagicMock()
        mock_button.is_displayed.return_value = True
        self.mock_driver.find_element.return_value = mock_button
        
        # Execute
        result = self.scraper.go_to_next_page()
        
        # Verify
        self.assertTrue(result)
        mock_button.click.assert_called_once()
    
    @patch('src.infrastructure.scrapers.duckduckgo_scraper.time.sleep')
    def test_go_to_next_page_no_button_scroll_fallback(self, mock_sleep):
        """Testa fallback para scroll quando não encontra botão"""
        # Setup mock - nenhum botão encontrado
        self.mock_driver.find_element.side_effect = Exception("Element not found")
        
        # Execute
        result = self.scraper.go_to_next_page()
        
        # Verify
        self.assertTrue(result)  # Deve retornar True mesmo sem botão
        # Verifica se execute_script foi chamado para scroll
        self.mock_driver.execute_script.assert_called()
    
    def test_go_to_next_page_exception_handling(self):
        """Testa tratamento de exceção no go_to_next_page"""
        # Setup mock - lança exceção geral
        self.mock_driver.execute_script.side_effect = Exception("General error")
        
        # Execute
        result = self.scraper.go_to_next_page()
        
        # Verify
        self.assertFalse(result)
    
    def test_get_result_links_exception_handling(self):
        """Testa tratamento de exceção no get_result_links"""
        # Setup mock - lança exceção
        self.mock_driver.execute_script.side_effect = Exception("Script error")
        self.mock_driver.find_elements.side_effect = Exception("Find error")
        
        # Execute
        links = self.scraper.get_result_links(["blacklisted.com"])
        
        # Verify - deve retornar lista vazia sem lançar exceção
        self.assertEqual(links, [])
    
    def test_extract_company_data_exception_handling(self):
        """Testa tratamento de exceção no extract_company_data"""
        # Setup mock - lança exceção
        self.mock_driver.execute_script.side_effect = Exception("Script error")
        
        # Execute
        result = self.scraper.extract_company_data("https://example.com", 5)
        
        # Verify - deve retornar CompanyModel vazio
        self.assertIsInstance(result, CompanyModel)
        self.assertEqual(result.url, "https://example.com")
        self.assertEqual(result.name, "")
        self.assertEqual(result.emails, "")
    
    def test_extract_company_data_finally_block_exception(self):
        """Testa bloco finally com exceção"""
        # Setup mock
        self.mock_driver.window_handles = ["tab1", "tab2"]
        self.mock_driver.close.side_effect = Exception("Close error")
        self.mock_driver.page_source = "Test page"
        self.mock_driver.title = "Test Company"
        
        # Execute
        result = self.scraper.extract_company_data("https://example.com", 5)
        
        # Verify - deve funcionar mesmo com erro no finally
        self.assertIsInstance(result, CompanyModel)
    
    def test_extract_emails_fast_exception_handling(self):
        """Testa tratamento de exceção no _extract_emails_fast"""
        # Setup mock - lança exceção ao acessar page_source
        type(self.mock_driver).page_source = PropertyMock(side_effect=Exception("Page source error"))
        
        # Execute
        emails = self.scraper._extract_emails_fast()
        
        # Verify - deve retornar lista vazia
        self.assertEqual(emails, [])
    
    def test_extract_phones_fast_exception_handling(self):
        """Testa tratamento de exceção no _extract_phones_fast"""
        # Setup mock - lança exceção ao acessar page_source
        type(self.mock_driver).page_source = PropertyMock(side_effect=Exception("Page source error"))
        
        # Execute
        phones = self.scraper._extract_phones_fast()
        
        # Verify - deve retornar lista vazia
        self.assertEqual(phones, [])
    
    def test_get_company_name_fast_exception_handling(self):
        """Testa tratamento de exceção no _get_company_name_fast"""
        # Setup mock - lança exceção ao acessar title
        type(self.mock_driver).title = PropertyMock(side_effect=Exception("Title error"))
        
        # Execute
        name = self.scraper._get_company_name_fast("https://example.com")
        
        # Verify - deve retornar domínio como fallback
        self.assertEqual(name, "example.com")
    
    def test_get_company_name_fast_empty_title(self):
        """Testa _get_company_name_fast com título vazio"""
        # Setup mock - título vazio
        self.mock_driver.title = ""
        
        # Execute
        name = self.scraper._get_company_name_fast("https://example.com")
        
        # Verify - deve retornar domínio como fallback
        self.assertEqual(name, "example.com")
    
    def test_is_blacklisted_true(self):
        """Testa _is_blacklisted retornando True"""
        # Execute
        result = self.scraper._is_blacklisted("https://blacklisted.com/page", ["blacklisted.com"])
        
        # Verify
        self.assertTrue(result)
    
    def test_is_blacklisted_false(self):
        """Testa _is_blacklisted retornando False"""
        # Execute
        result = self.scraper._is_blacklisted("https://example.com/page", ["blacklisted.com"])
        
        # Verify
        self.assertFalse(result)
    
    def test_extract_emails_fast_with_limit(self):
        """Testa _extract_emails_fast com limite de 5 e-mails"""
        # Setup mock page source com muitos e-mails
        emails_text = " ".join([f"email{i}@site.org" for i in range(10)])
        self.mock_driver.page_source = f"Contact: {emails_text}"
        
        # Execute
        emails = self.scraper._extract_emails_fast()
        
        # Verify - deve limitar a 5 e-mails
        self.assertLessEqual(len(emails), 5)
    
    def test_extract_phones_fast_with_limit(self):
        """Testa _extract_phones_fast com limite de 3 telefones"""
        # Setup mock page source com muitos telefones
        phones_text = " ".join([f"(11) 9876{i:04d}" for i in range(10)])
        self.mock_driver.page_source = f"Call us: {phones_text}"
        
        # Execute
        phones = self.scraper._extract_phones_fast()
        
        # Verify - deve limitar a 3 telefones
        self.assertLessEqual(len(phones), 3)
    
    def test_extract_phones_fast_pattern_break_conditions(self):
        """Testa condições de break nos padrões de telefone"""
        # Setup mock com telefones válidos para testar breaks
        valid_phones = "(11) 98765-4321 (21) 98765-4321 (31) 98765-4321 (41) 98765-4321"
        self.mock_driver.page_source = f"Contact: {valid_phones}"
        
        # Execute
        phones = self.scraper._extract_phones_fast()
        
        # Verify - deve encontrar telefones e respeitar limite
        self.assertLessEqual(len(phones), 3)
    
    def test_extract_emails_fast_pattern_break_conditions(self):
        """Testa condições de break nos padrões de e-mail"""
        # Setup mock com e-mails válidos para testar breaks
        valid_emails = "contact@site1.org info@site2.org admin@site3.org test@site4.org help@site5.org extra@site6.org"
        self.mock_driver.page_source = f"Contact: {valid_emails}"
        
        # Execute
        emails = self.scraper._extract_emails_fast()
        
        # Verify - deve encontrar e-mails e respeitar limite de 5
        self.assertLessEqual(len(emails), 5)


if __name__ == '__main__':
    unittest.main()