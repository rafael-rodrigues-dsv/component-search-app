"""
Testes completos para GoogleScraper
"""
import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import sys
import os

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src.infrastructure.scrapers.google_scraper import GoogleScraper
from src.domain.models.company_model import CompanyModel


class TestGoogleScraper(unittest.TestCase):
    """Testes para GoogleScraper"""
    
    def setUp(self):
        self.mock_driver = MagicMock()
        self.scraper = GoogleScraper(self.mock_driver)
    
    @patch('src.infrastructure.scrapers.google_scraper.WebDriverWait')
    @patch('src.infrastructure.scrapers.google_scraper.time.sleep')
    def test_search_success(self, mock_sleep, mock_wait):
        """Testa busca bem-sucedida no Google"""
        # Setup mocks
        mock_wait.return_value.until.return_value = MagicMock()
        
        # Execute
        result = self.scraper.search("test query")
        
        # Verify
        self.assertTrue(result)
        self.mock_driver.get.assert_called()
    
    def test_search_failure(self):
        """Testa falha na busca"""
        # Setup mock para lançar exceção
        self.mock_driver.get.side_effect = Exception("Search failed")
        
        # Execute
        result = self.scraper.search("test query")
        
        # Verify
        self.assertFalse(result)
    
    def test_get_result_links_success(self):
        """Testa extração de links do Google"""
        # Setup mock elements
        mock_link = MagicMock()
        mock_link.get_attribute.return_value = "https://example.com"
        self.mock_driver.find_elements.return_value = [mock_link]
        
        # Execute
        links = self.scraper.get_result_links(["blacklisted.com"])
        
        # Verify
        self.assertIn("https://example.com", links)
    
    def test_go_to_next_page(self):
        """Testa navegação para próxima página"""
        # Setup mock
        self.mock_driver.current_url = "https://google.com/search?q=test"
        
        # Execute
        result = self.scraper.go_to_next_page()
        
        # Verify
        self.mock_driver.get.assert_called()
    
    def test_extract_company_data_success(self):
        """Testa extração de dados da empresa"""
        # Setup mocks
        self.mock_driver.page_source = "Contact us at test@example.com"
        self.mock_driver.title = "Test Company"
        self.mock_driver.window_handles = ["tab1", "tab2"]
        
        # Execute
        result = self.scraper.extract_company_data("https://example.com", 5)
        
        # Verify
        self.assertIsInstance(result, CompanyModel)
        self.assertEqual(result.url, "https://example.com")
    
    def test_is_valid_url_valid(self):
        """Testa validação de URL válida"""
        valid_urls = [
            "https://example.com",
            "http://site.org",
            "https://empresa.com.br"
        ]
        
        for url in valid_urls:
            self.assertTrue(self.scraper._is_valid_url(url))
    
    def test_is_valid_url_invalid(self):
        """Testa validação de URL inválida"""
        invalid_urls = [
            "not-a-url",
            "https://google.com/search",
            "https://youtube.com/watch",
            None,
            ""
        ]
        
        for url in invalid_urls:
            self.assertFalse(self.scraper._is_valid_url(url))
    
    @patch('src.infrastructure.scrapers.google_scraper.WebDriverWait')
    def test_search_fallback_success(self, mock_wait):
        """Testa fallback quando busca principal falha"""
        # Setup mock - primeira busca falha, fallback funciona
        mock_wait.return_value.until.side_effect = Exception("Element not found")
        
        # Execute
        result = self.scraper.search("test query")
        
        # Verify - deve usar fallback e retornar True
        self.assertTrue(result)
    
    def test_fallback_search_simple_success(self):
        """Testa _fallback_search_simple com sucesso"""
        # Execute
        result = self.scraper._fallback_search_simple("test query")
        
        # Verify
        self.assertTrue(result)
    
    def test_fallback_search_simple_failure(self):
        """Testa _fallback_search_simple com falha"""
        # Setup mock para lançar exceção
        self.mock_driver.get.side_effect = Exception("Driver error")
        
        # Execute
        result = self.scraper._fallback_search_simple("test query")
        
        # Verify
        self.assertFalse(result)
    
    def test_get_result_links_with_selectors(self):
        """Testa get_result_links com diferentes seletores"""
        # Setup mock elements para diferentes seletores
        mock_link1 = MagicMock()
        mock_link1.get_attribute.return_value = "https://example1.com"
        mock_link2 = MagicMock()
        mock_link2.get_attribute.return_value = "https://example2.com"
        
        # Primeiro seletor retorna vazio, segundo retorna links
        self.mock_driver.find_elements.side_effect = [[], [mock_link1, mock_link2]]
        
        # Execute
        links = self.scraper.get_result_links(["blacklisted.com"])
        
        # Verify
        self.assertIn("https://example1.com", links)
        self.assertIn("https://example2.com", links)
    
    def test_get_result_links_exception_in_selector_loop(self):
        """Testa tratamento de exceção no loop de seletores"""
        # Setup mock para lançar exceção no find_elements
        self.mock_driver.find_elements.side_effect = Exception("Find error")
        
        # Execute
        links = self.scraper.get_result_links(["blacklisted.com"])
        
        # Verify - deve retornar lista vazia
        self.assertEqual(links, [])
    
    def test_get_result_links_exception_in_link_loop(self):
        """Testa tratamento de exceção no loop de links"""
        # Setup mock link que lança exceção
        mock_link = MagicMock()
        mock_link.get_attribute.side_effect = Exception("Attribute error")
        self.mock_driver.find_elements.return_value = [mock_link]
        
        # Execute
        links = self.scraper.get_result_links(["blacklisted.com"])
        
        # Verify - deve continuar e retornar lista vazia
        self.assertEqual(links, [])
    
    def test_go_to_next_page_with_existing_start(self):
        """Testa navegação com parâmetro start existente"""
        # Setup mock URL com start existente
        self.mock_driver.current_url = "https://google.com/search?q=test&start=10"
        
        # Execute
        result = self.scraper.go_to_next_page()
        
        # Verify
        self.mock_driver.get.assert_called()
    
    def test_go_to_next_page_without_start(self):
        """Testa navegação sem parâmetro start"""
        # Setup mock URL sem start
        self.mock_driver.current_url = "https://google.com/search?q=test"
        
        # Execute
        result = self.scraper.go_to_next_page()
        
        # Verify
        self.mock_driver.get.assert_called()
    
    @patch('src.infrastructure.scrapers.google_scraper.WebDriverWait')
    def test_go_to_next_page_wait_failure(self, mock_wait):
        """Testa falha no WebDriverWait do go_to_next_page"""
        # Setup mock
        self.mock_driver.current_url = "https://google.com/search?q=test"
        mock_wait.return_value.until.side_effect = Exception("Wait failed")
        
        # Execute
        result = self.scraper.go_to_next_page()
        
        # Verify - deve retornar False quando wait falha
        self.assertFalse(result)
    
    def test_go_to_next_page_general_exception(self):
        """Testa tratamento de exceção geral no go_to_next_page"""
        # Setup mock para lançar exceção geral
        self.mock_driver.current_url = "https://google.com/search?q=test"
        self.mock_driver.get.side_effect = Exception("General navigation error")
        
        # Execute
        result = self.scraper.go_to_next_page()
        
        # Verify - deve retornar False e imprimir aviso
        self.assertFalse(result)
    
    def test_extract_company_data_title_exception(self):
        """Testa tratamento de exceção ao obter título"""
        # Setup mock
        self.mock_driver.page_source = "Contact: test@example.com"
        type(self.mock_driver).title = PropertyMock(side_effect=Exception("Title error"))
        self.mock_driver.window_handles = ["tab1", "tab2"]
        
        # Execute
        result = self.scraper.extract_company_data("https://example.com", 5)
        
        # Verify - deve usar fallback para nome
        self.assertIsInstance(result, CompanyModel)
        self.assertEqual(result.name, "example.com")
    
    def test_extract_company_data_finally_exception(self):
        """Testa exceção no bloco finally"""
        # Setup mock
        self.mock_driver.page_source = "Test page"
        self.mock_driver.title = "Test Company"
        self.mock_driver.window_handles = ["tab1", "tab2"]
        self.mock_driver.close.side_effect = Exception("Close error")
        
        # Execute
        result = self.scraper.extract_company_data("https://example.com", 5)
        
        # Verify - deve funcionar mesmo com erro no finally
        self.assertIsInstance(result, CompanyModel)
    
    def test_extract_company_data_email_limit_break(self):
        """Testa break quando atinge limite de e-mails"""
        # Setup mock com muitos e-mails válidos
        emails_text = " ".join([f"email{i}@site.org" for i in range(10)])
        self.mock_driver.page_source = f"Contact: {emails_text}"
        self.mock_driver.title = "Test Company"
        self.mock_driver.window_handles = ["tab1", "tab2"]
        
        # Execute com limite baixo
        result = self.scraper.extract_company_data("https://example.com", 3)
        
        # Verify
        self.assertIsInstance(result, CompanyModel)
    
    def test_extract_phones_fast_exception(self):
        """Testa tratamento de exceção no _extract_phones_fast"""
        # Setup para lançar exceção
        with patch('re.findall', side_effect=Exception("Regex error")):
            # Execute
            phones = self.scraper._extract_phones_fast("test page")
            
            # Verify - deve retornar lista vazia
            self.assertEqual(phones, [])
    
    def test_extract_phones_fast_with_limit_break(self):
        """Testa break quando atinge limite de telefones"""
        # Setup com telefones válidos
        page_source = "(11) 98765-4321 (21) 98765-4321 (31) 98765-4321 (41) 98765-4321"
        
        # Execute
        phones = self.scraper._extract_phones_fast(page_source)
        
        # Verify - deve respeitar limite de 3
        self.assertLessEqual(len(phones), 3)
    
    def test_extract_company_data_general_exception(self):
        """Testa tratamento de exceção geral no extract_company_data"""
        # Setup mock para lançar exceção
        self.mock_driver.execute_script.side_effect = Exception("General error")
        
        # Execute
        result = self.scraper.extract_company_data("https://example.com", 5)
        
        # Verify - deve retornar CompanyModel com dados mínimos
        self.assertIsInstance(result, CompanyModel)
        self.assertEqual(result.url, "https://example.com")
        self.assertEqual(result.name, "")
        self.assertEqual(result.emails, "")
    
    def test_go_to_next_page_regex_no_match(self):
        """Testa go_to_next_page quando regex não encontra match"""
        # Setup mock URL com &start= mas sem número
        self.mock_driver.current_url = "https://google.com/search?q=test&start="
        
        # Execute
        result = self.scraper.go_to_next_page()
        
        # Verify - deve adicionar start=10
        self.mock_driver.get.assert_called()
    
    def test_extract_company_data_url_split_exception(self):
        """Testa tratamento quando URL não pode ser dividida"""
        # Setup mock
        self.mock_driver.page_source = "Test page"
        self.mock_driver.title = "Test Company"
        self.mock_driver.window_handles = ["tab1", "tab2"]
        
        # Execute com URL sem barras
        result = self.scraper.extract_company_data("invalid-url", 5)
        
        # Verify - deve usar URL como domínio
        self.assertIsInstance(result, CompanyModel)
        self.assertEqual(result.domain, "invalid-url")
    
    def test_extract_company_data_name_fallback(self):
        """Testa fallback do nome quando título é vazio"""
        # Setup mock
        self.mock_driver.page_source = "Test page"
        self.mock_driver.title = ""  # Título vazio
        self.mock_driver.window_handles = ["tab1", "tab2"]
        
        # Execute
        result = self.scraper.extract_company_data("https://example.com/page", 5)
        
        # Verify - deve usar domínio como nome
        self.assertIsInstance(result, CompanyModel)
        self.assertEqual(result.name, "example.com")
    
    @patch('re.findall')
    def test_extract_phones_fast_inner_break(self, mock_findall):
        """Testa break interno quando atinge 3 telefones por padrão"""
        # Setup mock para retornar exatamente 3 telefones válidos no primeiro padrão
        mock_findall.side_effect = [
            ['(11) 98765-4321', '(21) 98765-4321', '(31) 98765-4321'],  # Primeiro padrão - 3 telefones
            [],  # Outros padrões vazios
            [],
            []
        ]
        
        # Mock validation service para aceitar todos
        self.scraper.validation_service.is_valid_phone = MagicMock(return_value=True)
        
        # Execute
        phones = self.scraper._extract_phones_fast("test page")
        
        # Verify - deve encontrar exatamente 3 telefones e fazer break
        self.assertEqual(len(phones), 3)
    
    @patch('re.findall')
    def test_extract_phones_fast_outer_break(self, mock_findall):
        """Testa break externo quando atinge 3 telefones total"""
        # Setup mock para retornar telefones em padrões diferentes
        mock_findall.side_effect = [
            ['(11) 98765-4321', '(21) 98765-4321'],  # Primeiro padrão - 2 telefones
            ['(31) 98765-4321'],  # Segundo padrão - 1 telefone (total = 3)
            [],  # Outros padrões não devem ser executados
            []
        ]
        
        # Mock validation service para aceitar todos
        self.scraper.validation_service.is_valid_phone = MagicMock(return_value=True)
        
        # Execute
        phones = self.scraper._extract_phones_fast("test page")
        
        # Verify - deve encontrar exatamente 3 telefones e fazer break externo
        self.assertEqual(len(phones), 3)


if __name__ == '__main__':
    unittest.main()