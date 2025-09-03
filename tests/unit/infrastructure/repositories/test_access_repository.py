"""
Testes unitários para AccessRepository
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.infrastructure.repositories.access_repository import AccessRepository


class TestAccessRepository:
    """Testes para AccessRepository"""

    @pytest.fixture
    def repository(self):
        """Fixture do repositório"""
        with patch('src.infrastructure.repositories.access_repository.pyodbc'):
            return AccessRepository()

    @pytest.fixture
    def mock_connection(self):
        """Mock da conexão"""
        conn = Mock()
        cursor = Mock()
        conn.cursor.return_value = cursor
        conn.__enter__ = Mock(return_value=conn)
        conn.__exit__ = Mock(return_value=None)
        return conn, cursor

    def test_is_domain_visited_true(self, repository, mock_connection):
        """Testa verificação de domínio visitado - True"""
        conn, cursor = mock_connection
        cursor.fetchone.return_value = [1]

        with patch.object(repository, '_get_connection', return_value=conn):
            result = repository.is_domain_visited('example.com')

        assert result is True
        cursor.execute.assert_called_once()

    def test_save_empresa(self, repository, mock_connection):
        """Testa salvamento de empresa"""
        conn, cursor = mock_connection
        cursor.fetchone.return_value = [123]

        with patch.object(repository, '_get_connection', return_value=conn):
            empresa_id = repository.save_empresa(1, 'http://test.com', 'test.com', 'GOOGLE')

        assert empresa_id == 123
        assert cursor.execute.call_count == 2

    def test_is_email_collected(self, repository, mock_connection):
        """Testa verificação de e-mail coletado"""
        conn, cursor = mock_connection
        cursor.fetchone.return_value = [1]

        with patch.object(repository, '_get_connection', return_value=conn):
            result = repository.is_email_collected('test@example.com')

        assert result is True

    def test_get_pending_terms(self, repository, mock_connection):
        """Testa obtenção de termos pendentes"""
        conn, cursor = mock_connection
        cursor.fetchall.return_value = [
            (1, 'empresa de elevadores São Paulo', 'CAPITAL', 'PENDENTE')
        ]

        with patch.object(repository, '_get_connection', return_value=conn):
            terms = repository.get_pending_terms()

        assert len(terms) == 1
        assert terms[0]['id'] == 1
