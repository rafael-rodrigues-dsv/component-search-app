"""
Testes completos para DatabaseService
"""
import pytest
from unittest.mock import Mock, patch
from src.application.services.database_service import DatabaseService

class TestDatabaseServiceComplete:
    """Testes completos para DatabaseService"""
    
    @pytest.fixture
    def service(self):
        """Fixture do serviço"""
        with patch('src.application.services.database_service.AccessRepository'):
            return DatabaseService()
    
    def test_is_domain_visited(self, service):
        """Testa verificação de domínio visitado"""
        service.repository.is_domain_visited.return_value = False
        
        result = service.is_domain_visited('new.com')
        
        assert result is False
        service.repository.is_domain_visited.assert_called_once_with('new.com')
    
    def test_save_company_data_no_data(self, service):
        """Testa salvamento sem dados"""
        service.repository.save_empresa.return_value = 123
        
        result = service.save_company_data(
            termo_id=1,
            site_url='http://test.com',
            domain='test.com',
            motor_busca='GOOGLE',
            emails=[],
            telefones=[]
        )
        
        assert result is True
        service.repository.update_empresa_status.assert_called_with(123, 'SEM_DADOS', None)
    
    def test_save_company_data_with_name(self, service):
        """Testa salvamento com nome da empresa"""
        service.repository.save_empresa.return_value = 123
        
        result = service.save_company_data(
            termo_id=1,
            site_url='http://test.com',
            domain='test.com',
            motor_busca='GOOGLE',
            emails=['test@example.com'],
            telefones=[],
            nome_empresa='Test Company'
        )
        
        assert result is True
        service.repository.update_empresa_status.assert_called_with(123, 'COLETADO', 'Test Company')
    
    def test_get_search_terms(self, service):
        """Testa obtenção de termos de busca"""
        mock_terms = [
            {'id': 1, 'termo': 'test 1', 'tipo': 'CAPITAL', 'status': 'PENDENTE'},
            {'id': 2, 'termo': 'test 2', 'tipo': 'ZONA', 'status': 'PENDENTE'}
        ]
        service.repository.get_pending_terms.return_value = mock_terms
        
        terms = service.get_search_terms()
        
        assert len(terms) == 2
        assert terms[0]['id'] == 1
        service.repository.get_pending_terms.assert_called_once()
    
    def test_update_term_status(self, service):
        """Testa atualização de status do termo"""
        service.update_term_status(1, 'CONCLUIDO')
        
        service.repository.update_term_status.assert_called_once_with(1, 'CONCLUIDO')
    
    def test_reset_data_confirm(self, service):
        """Testa reset com confirmação"""
        service.reset_data(confirm=True)
        
        service.repository.reset_collected_data.assert_called_once()
    
    def test_reset_data_no_confirm(self, service):
        """Testa reset sem confirmação"""
        service.reset_data(confirm=False)
        
        service.repository.reset_collected_data.assert_not_called()
    
    def test_export_to_excel_failure(self, service):
        """Testa falha na exportação"""
        service.repository.export_to_excel.side_effect = Exception("Export failed")
        
        with patch('src.application.services.database_service.Path'):
            success, count = service.export_to_excel()
        
        assert success is False
        assert count == 0
    
    def test_export_to_excel_custom_path(self, service):
        """Testa exportação com caminho customizado"""
        service.repository.export_to_excel.return_value = 5
        
        success, count = service.export_to_excel('custom/path.xlsx')
        
        assert success is True
        assert count == 5
        # Verifica se foi chamado com algum caminho
        service.repository.export_to_excel.assert_called_once()
    
    def test_get_statistics_empty(self, service):
        """Testa estatísticas quando não há dados"""
        mock_cursor = Mock()
        mock_cursor.fetchone.side_effect = [
            [0], [0], [0], [0], [0], [0]  # Todos zeros
        ]
        
        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        
        service.repository._get_connection.return_value = mock_conn
        
        stats = service.get_statistics()
        
        assert stats['termos_total'] == 0
        assert stats['progresso_pct'] == 0.0
    
    def test_get_statistics_exception(self, service):
        """Testa exceção ao obter estatísticas"""
        service.repository._get_connection.side_effect = Exception("DB Error")
        
        stats = service.get_statistics()
        
        assert stats is None
    
    def test_save_company_data_exception(self, service):
        """Testa exceção no salvamento"""
        service.repository.save_empresa.side_effect = Exception("Save failed")
        
        result = service.save_company_data(
            termo_id=1,
            site_url='http://test.com',
            domain='test.com',
            motor_busca='GOOGLE',
            emails=['test@example.com'],
            telefones=[]
        )
        
        assert result is False