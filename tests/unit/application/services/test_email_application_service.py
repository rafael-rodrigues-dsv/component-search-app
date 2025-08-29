"""
Testes unitários para EmailApplicationService
"""
import unittest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.application.services.email_application_service import EmailApplicationService
from src.domain.models.search_term_model import SearchTermModel
from src.domain.models.company_model import CompanyModel


class TestEmailApplicationService(unittest.TestCase):
    """Testes para EmailApplicationService"""
    
    def setUp(self):
        """Setup para cada teste"""
        # Mock todas as dependências externas
        self.patches = []
        
        # Mock UserConfigService
        self.mock_user_config = patch('src.application.services.email_application_service.UserConfigService')
        self.mock_user_config_cls = self.mock_user_config.start()
        self.mock_user_config_cls.get_search_engine.return_value = "DUCKDUCKGO"
        self.mock_user_config_cls.get_restart_option.return_value = False
        self.mock_user_config_cls.get_processing_mode.return_value = 10
        self.patches.append(self.mock_user_config)
        
        # Mock DataStorage
        self.mock_data_storage = patch('src.application.services.email_application_service.DataStorage')
        self.mock_data_storage_cls = self.mock_data_storage.start()
        self.patches.append(self.mock_data_storage)
        
        # Mock WebDriverManager
        self.mock_web_driver = patch('src.application.services.email_application_service.WebDriverManager')
        self.mock_web_driver_cls = self.mock_web_driver.start()
        self.mock_driver_instance = Mock()
        self.mock_web_driver_cls.return_value = self.mock_driver_instance
        self.patches.append(self.mock_web_driver)
        
        # Mock Scrapers
        self.mock_duckduckgo = patch('src.application.services.email_application_service.DuckDuckGoScraper')
        self.mock_duckduckgo_cls = self.mock_duckduckgo.start()
        self.mock_scraper_instance = Mock()
        self.mock_duckduckgo_cls.return_value = self.mock_scraper_instance
        self.patches.append(self.mock_duckduckgo)
        
        self.mock_google = patch('src.application.services.email_application_service.GoogleScraper')
        self.mock_google_cls = self.mock_google.start()
        self.patches.append(self.mock_google)
        
        # Mock Repositories
        self.mock_json_repo = patch('src.application.services.email_application_service.JsonRepository')
        self.mock_json_repo_cls = self.mock_json_repo.start()
        self.mock_json_instance = Mock()
        self.mock_json_instance.load_visited_domains.return_value = {}
        self.mock_json_instance.load_seen_emails.return_value = set()
        self.mock_json_repo_cls.return_value = self.mock_json_instance
        self.patches.append(self.mock_json_repo)
        
        self.mock_excel_repo = patch('src.application.services.email_application_service.ExcelRepository')
        self.mock_excel_repo_cls = self.mock_excel_repo.start()
        self.mock_excel_instance = Mock()
        self.mock_excel_repo_cls.return_value = self.mock_excel_instance
        self.patches.append(self.mock_excel_repo)
        
        # Mock Services
        self.mock_working_hours = patch('src.application.services.email_application_service.WorkingHoursService')
        self.mock_working_hours_cls = self.mock_working_hours.start()
        self.mock_working_hours_instance = Mock()
        self.mock_working_hours_instance.is_working_time.return_value = True
        self.mock_working_hours_cls.return_value = self.mock_working_hours_instance
        self.patches.append(self.mock_working_hours)
        
        self.mock_validation = patch('src.application.services.email_application_service.EmailValidationService')
        self.mock_validation_cls = self.mock_validation.start()
        self.mock_validation_instance = Mock()
        self.mock_validation_instance.extract_domain_from_url.return_value = "example.com"
        self.mock_validation_cls.return_value = self.mock_validation_instance
        self.patches.append(self.mock_validation)
        

        
        # Mock SearchTermFactory
        self.mock_search_factory = patch('src.application.services.email_application_service.SearchTermFactory')
        self.mock_search_factory_cls = self.mock_search_factory.start()
        self.mock_search_factory_cls.create_search_terms.return_value = [
            SearchTermModel("test query", "SP", "elevadores", 1)
        ]
        self.patches.append(self.mock_search_factory)
        
        # Mock time.sleep e random.uniform
        self.mock_sleep = patch('time.sleep')
        self.mock_sleep.start()
        self.patches.append(self.mock_sleep)
        
        self.mock_random = patch('random.uniform')
        self.mock_random_cls = self.mock_random.start()
        self.mock_random_cls.return_value = 1.0
        self.patches.append(self.mock_random)
    
    def tearDown(self):
        """Cleanup após cada teste"""
        for patch_obj in self.patches:
            patch_obj.stop()
    
    def test_init_with_duckduckgo_engine(self):
        """Testa inicialização com motor DuckDuckGo"""
        service = EmailApplicationService()
        
        self.assertEqual(service.search_engine, "DUCKDUCKGO")
        self.mock_duckduckgo_cls.assert_called_once()
        self.assertIsInstance(service.scraper, Mock)
    
    def test_init_with_google_engine(self):
        """Testa inicialização com motor Google"""
        self.mock_user_config_cls.get_search_engine.return_value = "GOOGLE"
        
        service = EmailApplicationService()
        
        self.assertEqual(service.search_engine, "GOOGLE")
        self.mock_google_cls.assert_called_once_with(None)
    
    def test_init_with_restart_option_true(self):
        """Testa inicialização com opção de restart"""
        self.mock_user_config_cls.get_restart_option.return_value = True
        
        service = EmailApplicationService()
        
        self.mock_data_storage_cls.clear_all_data.assert_called_once()
    
    def test_init_with_ignore_working_hours(self):
        """Testa inicialização ignorando horário de trabalho"""
        service = EmailApplicationService(ignore_working_hours=True)
        
        self.assertTrue(service.ignore_working_hours)
    
    def test_setup_scraper_duckduckgo(self):
        """Testa configuração do scraper DuckDuckGo"""
        service = EmailApplicationService()
        service.search_engine = "DUCKDUCKGO"
        
        service._setup_scraper()
        
        self.mock_duckduckgo_cls.assert_called()
    
    def test_setup_scraper_google(self):
        """Testa configuração do scraper Google"""
        service = EmailApplicationService()
        service.search_engine = "GOOGLE"
        
        service._setup_scraper()
        
        self.mock_google_cls.assert_called_with(None)
    
    def test_setup_repositories(self):
        """Testa configuração dos repositórios"""
        service = EmailApplicationService()
        
        service._setup_repositories()
        
        self.mock_json_repo_cls.assert_called()
        self.mock_excel_repo_cls.assert_called()
    
    def test_setup_services(self):
        """Testa configuração dos serviços"""
        service = EmailApplicationService()
        
        service._setup_services(ignore_working_hours=True)
        
        self.assertTrue(service.ignore_working_hours)
        self.mock_working_hours_cls.assert_called()
        self.mock_validation_cls.assert_called()
    
    def test_execute_success(self):
        """Testa execução bem-sucedida"""
        service = EmailApplicationService()
        service.driver_manager.start_driver.return_value = True
        service.scraper = Mock()
        
        with patch.object(service, 'collect_emails', return_value=True) as mock_collect:
            result = service.execute()
            
            self.assertTrue(result)
            service.driver_manager.start_driver.assert_called_once()
            mock_collect.assert_called_once()
            service.driver_manager.close_driver.assert_called_once()
    
    def test_execute_chromedriver_failure(self):
        """Testa falha no driver start"""
        service = EmailApplicationService()
        service.driver_manager.start_driver.return_value = False
        
        result = service.execute()
        
        self.assertFalse(result)
        service.driver_manager.close_driver.assert_called_once()
    
    def test_execute_driver_start_failure(self):
        """Testa falha ao iniciar driver"""
        service = EmailApplicationService()
        service.driver_manager.start_driver.return_value = False
        
        result = service.execute()
        
        self.assertFalse(result)
        service.driver_manager.close_driver.assert_called_once()
    
    def test_execute_with_google_engine(self):
        """Testa execução com motor Google"""
        self.mock_user_config_cls.get_search_engine.return_value = "GOOGLE"
        
        service = EmailApplicationService()
        service.driver_manager.start_driver.return_value = True
        service.scraper = Mock()
        
        with patch.object(service, 'collect_emails', return_value=True):
            service.execute()
            
            # Verifica se o driver foi atribuído ao scraper Google
            self.assertEqual(service.scraper.driver, service.driver_manager.driver)
    
    def test_collect_emails_success(self):
        """Testa coleta de e-mails bem-sucedida"""
        service = EmailApplicationService()
        service.top_results_total = 10
        
        terms = [SearchTermModel("test", "SP", "elevadores", 1)]
        
        with patch.object(service, '_process_term_results', return_value=2):
            result = service.collect_emails(terms)
            
            self.assertTrue(result)
    
    def test_collect_emails_with_working_hours_check(self):
        """Testa coleta respeitando horário de trabalho"""
        service = EmailApplicationService()
        service.ignore_working_hours = False
        service.working_hours.is_working_time.return_value = False
        service.top_results_total = 10
        
        terms = [SearchTermModel("test", "SP", "elevadores", 1)]
        
        # Mock para simular que após primeira verificação está no horário
        def side_effect():
            service.working_hours.is_working_time.return_value = True
            return True
        
        service.working_hours.is_working_time.side_effect = [False, True]
        
        with patch.object(service, '_process_term_results', return_value=1):
            result = service.collect_emails(terms)
            
            self.assertTrue(result)
    
    def test_process_term_results_success(self):
        """Testa processamento de resultados de termo"""
        service = EmailApplicationService()
        service.top_results_total = 10
        service.visited_domains = {}
        service.seen_emails = set()
        
        # Mock scraper
        service.scraper = Mock()
        service.scraper.get_result_links.return_value = ["http://example.com"]
        
        # Mock company
        mock_company = CompanyModel(
            name="Test Company",
            emails="test@example.com;",
            domain="example.com",
            url="http://example.com",
            phone="(11) 99999-9999;"
        )
        service.scraper.extract_company_data.return_value = mock_company
        
        with patch.object(service, '_save_company_if_valid', return_value=True):
            with patch.object(service, '_save_progress'):
                term = SearchTermModel("test", "SP", "elevadores", 1)
                result = service._process_term_results(term, 100, 0)
                
                self.assertEqual(result, 1)
    
    def test_process_term_results_no_links(self):
        """Testa processamento quando não há links"""
        service = EmailApplicationService()
        service.scraper = Mock()
        service.scraper.get_result_links.return_value = []
        
        term = SearchTermModel("test", "SP", "elevadores", 1)
        result = service._process_term_results(term, 100, 0)
        
        self.assertEqual(result, 0)
    
    def test_process_term_results_visited_domain(self):
        """Testa processamento com domínio já visitado"""
        service = EmailApplicationService()
        service.top_results_total = 10
        service.visited_domains = {"example.com": True}
        service.scraper = Mock()
        service.scraper.get_result_links.return_value = ["http://example.com"]
        
        term = SearchTermModel("test", "SP", "elevadores", 1)
        result = service._process_term_results(term, 100, 0)
        
        self.assertEqual(result, 0)
    
    def test_save_company_if_valid_success(self):
        """Testa salvamento de empresa válida"""
        service = EmailApplicationService()
        service.seen_emails = set()
        service.excel_repo = Mock()
        
        company = CompanyModel(
            name="Test",
            emails="test@example.com;new@example.com;",
            domain="example.com",
            url="http://example.com",
            phone=""
        )
        
        result = service._save_company_if_valid(company, "example.com")
        
        self.assertTrue(result)
        service.excel_repo.save_company.assert_called_once()
        self.assertIn("test@example.com", service.seen_emails)
        self.assertIn("new@example.com", service.seen_emails)
    
    def test_save_company_if_valid_no_emails(self):
        """Testa salvamento com empresa sem e-mails"""
        service = EmailApplicationService()
        
        company = CompanyModel(
            name="Test",
            emails="",
            domain="example.com",
            url="http://example.com",
            phone=""
        )
        
        result = service._save_company_if_valid(company, "example.com")
        
        self.assertFalse(result)
    
    def test_save_company_if_valid_emails_already_seen(self):
        """Testa salvamento com e-mails já coletados"""
        service = EmailApplicationService()
        service.seen_emails = {"test@example.com"}
        
        company = CompanyModel(
            name="Test",
            emails="test@example.com;",
            domain="example.com",
            url="http://example.com",
            phone=""
        )
        
        result = service._save_company_if_valid(company, "example.com")
        
        self.assertFalse(result)
    
    def test_save_progress(self):
        """Testa salvamento de progresso"""
        service = EmailApplicationService()
        service.json_repo = Mock()
        service.visited_domains = {"example.com": True}
        service.seen_emails = {"test@example.com"}
        
        service._save_progress()
        
        service.json_repo.save_visited_domains.assert_called_once_with(service.visited_domains)
        service.json_repo.save_seen_emails.assert_called_once_with(service.seen_emails)
    
    def test_collect_emails_interface_implementation(self):
        """Testa se implementa corretamente a interface EmailCollectorInterface"""
        service = EmailApplicationService()
        
        # Verifica se o método collect_emails existe e é chamável
        self.assertTrue(hasattr(service, 'collect_emails'))
        self.assertTrue(callable(getattr(service, 'collect_emails')))
    
    def test_process_term_results_with_pagination(self):
        """Testa processamento com paginação"""
        service = EmailApplicationService()
        service.top_results_total = 10
        service.visited_domains = {}
        service.scraper = Mock()
        service.scraper.get_result_links.return_value = ["http://example.com"]
        service.scraper.go_to_next_page.return_value = False
        
        mock_company = CompanyModel(
            name="Test",
            emails="test@example.com;",
            domain="example.com",
            url="http://example.com",
            phone=""
        )
        service.scraper.extract_company_data.return_value = mock_company
        
        with patch.object(service, '_save_company_if_valid', return_value=True):
            with patch.object(service, '_save_progress'):
                term = SearchTermModel("test", "SP", "elevadores", 2)  # 2 páginas
                result = service._process_term_results(term, 100, 0)
                
                # Verifica se tentou ir para próxima página
                service.scraper.go_to_next_page.assert_called()
    
    def test_collect_emails_search_failure(self):
        """Testa coleta quando busca falha"""
        service = EmailApplicationService()
        service.scraper = Mock()
        service.scraper.search.return_value = False
        
        terms = [SearchTermModel("test", "SP", "elevadores", 1)]
        result = service.collect_emails(terms)
        
        self.assertTrue(result)  # Deve continuar mesmo com falha
    
    def test_process_term_results_no_go_to_next_page_method(self):
        """Testa processamento quando scraper não tem go_to_next_page"""
        service = EmailApplicationService()
        service.top_results_total = 10
        service.visited_domains = {}
        service.scraper = Mock()
        service.scraper.get_result_links.return_value = ["http://example.com"]
        
        # Remove o método go_to_next_page
        del service.scraper.go_to_next_page
        
        mock_company = CompanyModel(
            name="Test",
            emails="test@example.com;",
            domain="example.com",
            url="http://example.com",
            phone=""
        )
        service.scraper.extract_company_data.return_value = mock_company
        
        with patch.object(service, '_save_company_if_valid', return_value=True):
            with patch.object(service, '_save_progress'):
                term = SearchTermModel("test", "SP", "elevadores", 2)
                result = service._process_term_results(term, 100, 0)
                
                # Não deve lançar exceção
                self.assertEqual(result, 1)
    
    def test_collect_emails_complete_mode(self):
        """Testa coleta em modo completo (> 1000)"""
        service = EmailApplicationService()
        service.top_results_total = 999999  # Modo completo
        
        terms = [SearchTermModel("test", "SP", "elevadores", 1)]
        
        with patch.object(service, '_process_term_results', return_value=1):
            result = service.collect_emails(terms)
            
            self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()