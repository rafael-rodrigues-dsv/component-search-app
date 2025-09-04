"""
Testes completos para AccessRepository
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.infrastructure.repositories.access_repository import AccessRepository


class TestAccessRepositoryComplete:
    """Testes completos para AccessRepository"""

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

    def test_is_domain_visited_false(self, repository, mock_connection):
        """Testa verificação de domínio não visitado"""
        conn, cursor = mock_connection
        cursor.fetchone.return_value = [0]

        with patch.object(repository, '_get_connection', return_value=conn):
            result = repository.is_domain_visited('new.com')

        assert result is False

    def test_update_empresa_status_with_name(self, repository, mock_connection):
        """Testa atualização de status com nome"""
        conn, cursor = mock_connection

        with patch.object(repository, '_get_connection', return_value=conn):
            repository.update_empresa_status(123, 'COLETADO', 'Test Company')

        cursor.execute.assert_called_once()
        conn.commit.assert_called_once()

    def test_update_empresa_status_without_name(self, repository, mock_connection):
        """Testa atualização de status sem nome"""
        conn, cursor = mock_connection

        with patch.object(repository, '_get_connection', return_value=conn):
            repository.update_empresa_status(123, 'ERRO')

        cursor.execute.assert_called_once()
        conn.commit.assert_called_once()

    def test_save_emails_with_duplicates(self, repository, mock_connection):
        """Testa salvamento de e-mails com duplicatas"""
        conn, cursor = mock_connection

        with patch.object(repository, '_get_connection', return_value=conn):
            with patch.object(repository, 'is_email_collected', side_effect=[False, True, False]):
                repository.save_emails(1, ['new@test.com', 'old@test.com', 'another@test.com'], 'test.com')

        # Deve salvar apenas 2 (new e another)
        assert cursor.execute.call_count == 2
        conn.commit.assert_called_once()

    def test_save_telefones(self, repository, mock_connection):
        """Testa salvamento de telefones"""
        conn, cursor = mock_connection
        telefones = [
            {'original': '11999999999', 'formatted': '(11) 99999-9999', 'ddd': '11', 'tipo': 'CELULAR'},
            {'original': '1133334444', 'formatted': '(11) 3333-4444', 'ddd': '11', 'tipo': 'FIXO'}
        ]

        with patch.object(repository, '_get_connection', return_value=conn):
            repository.save_telefones(1, telefones)

        assert cursor.execute.call_count == 2
        conn.commit.assert_called_once()

    def test_update_term_status(self, repository, mock_connection):
        """Testa atualização de status do termo"""
        conn, cursor = mock_connection

        with patch.object(repository, '_get_connection', return_value=conn):
            repository.update_term_status(1, 'CONCLUIDO')

        cursor.execute.assert_called_once()
        conn.commit.assert_called_once()

    def test_generate_search_terms_complete(self, repository, mock_connection):
        """Testa geração completa de termos"""
        conn, cursor = mock_connection

        # Mock dos dados
        cursor.fetchall.side_effect = [
            [(1, 'empresa de elevadores'), (2, 'manutenção de elevadores')],  # bases
            [(1, 'zona norte'), (2, 'zona sul')],  # zonas
            [(1, 'Moema'), (2, 'Vila Mariana')],  # bairros
            [(1, 'Campinas'), (2, 'Guarulhos')]  # cidades
        ]
        cursor.fetchone.return_value = [20]  # count final

        with patch.object(repository, '_get_connection', return_value=conn):
            count = repository.generate_search_terms()

        assert count == 20
        # Verifica DELETE inicial + múltiplos INSERTs
        assert cursor.execute.call_count >= 10
        conn.commit.assert_called_once()

    def test_reset_collected_data(self, repository, mock_connection):
        """Testa reset completo"""
        conn, cursor = mock_connection

        with patch.object(repository, '_get_connection', return_value=conn):
            repository.reset_collected_data()

        # 4 operações: 3 DELETEs + 1 UPDATE
        assert cursor.execute.call_count == 4
        conn.commit.assert_called_once()

    def test_export_to_excel(self, repository, mock_connection):
        """Testa exportação para Excel"""
        conn, cursor = mock_connection
        cursor.fetchall.return_value = [
            ('http://test.com', 'test@example.com;', '(11) 99999-9999;', 'Rua Test, 123', 5.2),
            ('http://test2.com', 'test2@example.com;', '(11) 88888-8888;', 'Rua Test2, 456', 10.5)
        ]

        with patch.object(repository, '_get_connection', return_value=conn):
            with patch('openpyxl.Workbook') as mock_workbook:
                mock_wb = Mock()
                mock_ws = Mock()
                # Configurar mock para suportar item assignment
                mock_ws.__setitem__ = Mock()
                mock_wb.active = mock_ws
                mock_workbook.return_value = mock_wb

                count = repository.export_to_excel('test.xlsx')

        assert count == 2
        mock_wb.save.assert_called_once_with('test.xlsx')
        cursor.execute.assert_called_once()

    def test_get_connection(self, repository):
        """Testa obtenção de conexão"""
        with patch('src.infrastructure.repositories.access_repository.pyodbc') as mock_pyodbc:
            mock_conn = Mock()
            mock_pyodbc.connect.return_value = mock_conn

            conn = repository._get_connection()

            assert conn == mock_conn
            mock_pyodbc.connect.assert_called_once_with(repository.conn_str)

    def test_db_path_construction(self, repository):
        """Testa construção do caminho do banco"""
        assert 'pythonsearch.accdb' in str(repository.db_path)
        assert 'data' in str(repository.db_path)

    def test_conn_str_format(self, repository):
        """Testa formato da string de conexão"""
        assert 'Microsoft Access Driver' in repository.conn_str
        assert 'pythonsearch.accdb' in repository.conn_str
