"""
Utilitários para testes
"""
from unittest.mock import Mock, patch
from typing import List, Dict, Any


class MockHelper:
    """Helper para criar mocks padronizados"""

    @staticmethod
    def create_mock_scraper(return_links: List[str] = None, return_company: Any = None):
        """Cria mock do scraper"""
        mock_scraper = Mock()
        mock_scraper.search.return_value = True
        mock_scraper.get_result_links.return_value = return_links or []
        mock_scraper.extract_company_data.return_value = return_company
        mock_scraper.go_to_next_page.return_value = False
        return mock_scraper

    @staticmethod
    def create_mock_repository():
        """Cria mock do repositório"""
        mock_repo = Mock()
        mock_repo.load_visited_domains.return_value = {}
        mock_repo.load_seen_emails.return_value = set()
        return mock_repo

    @staticmethod
    def create_mock_driver_manager():
        """Cria mock do driver manager"""
        mock_driver = Mock()
        mock_driver.start_driver.return_value = True
        mock_driver.close_driver.return_value = None
        return mock_driver


class AssertHelper:
    """Helper para assertions customizadas"""

    @staticmethod
    def assert_mock_called_with_any(mock_obj, *expected_args):
        """Verifica se mock foi chamado com qualquer um dos argumentos"""
        calls = mock_obj.call_args_list
        for call in calls:
            if any(arg in str(call) for arg in expected_args):
                return True
        raise AssertionError(f"Mock não foi chamado com nenhum dos argumentos esperados: {expected_args}")

    @staticmethod
    def assert_email_format(email_string: str):
        """Verifica formato de e-mail com ';' no final"""
        assert email_string.endswith(';'), f"E-mail deve terminar com ';': {email_string}"
        emails = [e.strip() for e in email_string.split(';') if e.strip()]
        for email in emails:
            assert '@' in email, f"E-mail inválido: {email}"
