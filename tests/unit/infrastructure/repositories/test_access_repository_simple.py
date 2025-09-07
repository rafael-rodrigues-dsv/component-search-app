"""
Testes simples para AccessRepository
"""
import pytest
from unittest.mock import Mock, patch
from src.domain.models.address_model import AddressModel


class TestAccessRepositorySimple:
    """Testes simples para AccessRepository"""

    def setup_method(self):
        """Setup para cada teste"""
        with patch('src.infrastructure.repositories.access_repository.pyodbc'):
            from src.infrastructure.repositories.access_repository import AccessRepository
            self.repository = AccessRepository()

    def test_is_domain_visited_true(self):
        """Testa domínio visitado"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        
        mock_cursor.fetchone.return_value = [1]
        
        with patch.object(self.repository, '_get_connection', return_value=mock_conn):
            result = self.repository.is_domain_visited('test.com')
        
        assert result is True

    def test_is_domain_visited_false(self):
        """Testa domínio não visitado"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        
        mock_cursor.fetchone.return_value = [0]
        
        with patch.object(self.repository, '_get_connection', return_value=mock_conn):
            result = self.repository.is_domain_visited('test.com')
        
        assert result is False

    def test_save_endereco_success(self):
        """Testa salvamento de endereço"""
        address = AddressModel(
            logradouro="Rua Test",
            numero="123",
            bairro="Centro",
            cidade="São Paulo",
            estado="SP"
        )
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        
        # Mock verificação de existência (não existe)
        mock_cursor.fetchone.side_effect = [None, [123]]
        
        with patch.object(self.repository, '_get_connection', return_value=mock_conn):
            result = self.repository.save_endereco(address)
        
        assert result == 123

    def test_save_endereco_existing(self):
        """Testa endereço já existente"""
        address = AddressModel(logradouro="Rua Test", numero="123")
        
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        
        # Mock endereço já existe
        mock_cursor.fetchone.return_value = [456]
        
        with patch.object(self.repository, '_get_connection', return_value=mock_conn):
            result = self.repository.save_endereco(address)
        
        assert result == 456

    def test_save_endereco_invalid(self):
        """Testa endereço inválido"""
        result = self.repository.save_endereco(None)
        assert result is None

    def test_save_endereco_exception(self):
        """Testa exceção no salvamento"""
        address = AddressModel(logradouro="Test")
        
        with patch.object(self.repository, '_get_connection', side_effect=Exception("DB Error")):
            result = self.repository.save_endereco(address)
        
        assert result is None

    def test_is_email_collected_true(self):
        """Testa email já coletado"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        
        mock_cursor.fetchone.return_value = [1]
        
        with patch.object(self.repository, '_get_connection', return_value=mock_conn):
            result = self.repository.is_email_collected('test@test.com')
        
        assert result is True

    def test_save_emails_success(self):
        """Testa salvamento de emails"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        
        emails = ['test1@test.com', 'test2@test.com']
        
        with patch.object(self.repository, '_get_connection', return_value=mock_conn):
            self.repository.save_emails(1, emails, 'test.com')
        
        mock_cursor.executemany.assert_called_once()
        mock_conn.commit.assert_called_once()

    def test_save_emails_empty(self):
        """Testa salvamento sem emails"""
        with patch.object(self.repository, '_get_connection') as mock_conn:
            self.repository.save_emails(1, [], 'test.com')
        
        # Não deve chamar conexão se não há emails
        mock_conn.assert_not_called()

    def test_save_telefones_success(self):
        """Testa salvamento de telefones"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        
        telefones = [
            {'original': '11999998888', 'formatted': '(11) 99999-8888', 'ddd': '11', 'tipo': 'CELULAR'}
        ]
        
        with patch.object(self.repository, '_get_connection', return_value=mock_conn):
            self.repository.save_telefones(1, telefones)
        
        mock_cursor.executemany.assert_called_once()

    def test_get_pending_terms_success(self):
        """Testa obtenção de termos pendentes"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        
        mock_cursor.fetchall.return_value = [
            (1, 'termo test', 'CAPITAL', 'PENDENTE')
        ]
        
        with patch.object(self.repository, '_get_connection', return_value=mock_conn):
            result = self.repository.get_pending_terms()
        
        assert len(result) == 1
        assert result[0]['id'] == 1
        assert result[0]['termo'] == 'termo test'

    def test_update_term_status_success(self):
        """Testa atualização de status do termo"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        
        with patch.object(self.repository, '_get_connection', return_value=mock_conn):
            self.repository.update_term_status(1, 'CONCLUIDO')
        
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    def test_reset_collected_data_success(self):
        """Testa reset de dados coletados"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        
        with patch.object(self.repository, '_get_connection', return_value=mock_conn):
            self.repository.reset_collected_data()
        
        # Deve executar 5 comandos DELETE/UPDATE
        assert mock_cursor.execute.call_count == 5
        mock_conn.commit.assert_called_once()

    def test_create_geolocation_task_success(self):
        """Testa criação de tarefa de geolocalização"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        
        # Mock não existe tarefa
        mock_cursor.fetchone.return_value = None
        
        with patch.object(self.repository, '_get_connection', return_value=mock_conn):
            self.repository.create_geolocation_task(1, 123)
        
        assert mock_cursor.execute.call_count == 2  # SELECT + INSERT
        mock_conn.commit.assert_called_once()

    def test_create_geolocation_task_existing(self):
        """Testa tarefa já existente"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=None)
        
        # Mock tarefa já existe
        mock_cursor.fetchone.return_value = [1]
        
        with patch.object(self.repository, '_get_connection', return_value=mock_conn):
            self.repository.create_geolocation_task(1, 123)
        
        # Só deve fazer SELECT, não INSERT
        assert mock_cursor.execute.call_count == 1

    def test_create_geolocation_task_no_endereco_id(self):
        """Testa sem ID de endereço"""
        with patch.object(self.repository, '_get_connection') as mock_conn:
            self.repository.create_geolocation_task(1, None)
        
        # Não deve chamar conexão
        mock_conn.assert_not_called()

    def test_close_connection_success(self):
        """Testa fechamento de conexão"""
        mock_conn = Mock()
        self.repository._connection = mock_conn
        
        self.repository.close_connection()
        
        mock_conn.close.assert_called_once()
        assert self.repository._connection is None

    def test_close_connection_no_connection(self):
        """Testa fechamento sem conexão"""
        self.repository._connection = None
        
        # Não deve dar erro
        self.repository.close_connection()
        
        assert self.repository._connection is None