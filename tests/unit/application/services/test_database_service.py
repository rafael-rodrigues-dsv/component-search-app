"""
Testes unitários para DatabaseService
"""
import pytest
from unittest.mock import Mock, patch
from src.application.services.database_service import DatabaseService


class TestDatabaseService:
    """Testes para DatabaseService"""

    @pytest.fixture
    def service(self):
        """Fixture do serviço"""
        with patch('src.application.services.database_service.AccessRepository'):
            return DatabaseService()

    def test_initialize_search_terms_new(self, service):
        """Testa inicialização de termos - primeira vez"""
        service.repository.get_pending_terms.return_value = []
        service.repository.generate_search_terms.return_value = 336

        count = service.initialize_search_terms()

        assert count == 336
        service.repository.generate_search_terms.assert_called_once()

    def test_initialize_search_terms_existing(self, service):
        """Testa inicialização de termos - já existem"""
        service.repository.get_pending_terms.return_value = [
            {'id': 1, 'termo': 'test', 'tipo': 'CAPITAL', 'status': 'PENDENTE'}
        ]

        count = service.initialize_search_terms()

        assert count == 1
        service.repository.generate_search_terms.assert_not_called()

    def test_save_company_data_success(self, service):
        """Testa salvamento de dados da empresa - sucesso"""
        service.repository.save_empresa.return_value = 123

        result = service.save_company_data(
            termo_id=1,
            site_url='http://test.com',
            domain='test.com',
            motor_busca='GOOGLE',
            emails=['test@example.com'],
            telefones=[{'original': '11999999999', 'formatted': '(11) 99999-9999'}]
        )

        assert result is True
        service.repository.save_empresa.assert_called_once()
        service.repository.save_emails.assert_called_once()
        service.repository.save_telefones.assert_called_once()
        service.repository.update_empresa_status.assert_called_once()

    def test_export_to_excel_success(self, service):
        """Testa exportação para Excel - sucesso"""
        service.repository.export_to_excel.return_value = 10

        with patch('src.application.services.database_service.Path'):
            success, count = service.export_to_excel()

        assert success is True
        assert count == 10
