"""
Testes unitários simplificados para DataStorage
"""
import os
import sys
import unittest
from unittest.mock import patch

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))


class TestDataStorage(unittest.TestCase):
    """Testes para DataStorage"""

    @patch('src.infrastructure.storage.data_storage.os.makedirs')
    @patch('src.infrastructure.storage.data_storage.os.path.exists')
    @patch('src.infrastructure.storage.data_storage.os.remove')
    def test_clear_all_data_basic_functionality(self, mock_remove, mock_exists, mock_makedirs):
        """Testa funcionalidade básica de limpeza"""
        from src.infrastructure.storage.data_storage import DataStorage

        mock_exists.return_value = True

        DataStorage.clear_all_data()

        # Verifica se makedirs foi chamado
        mock_makedirs.assert_called()
        # Verifica se remove foi chamado (pelo menos uma vez)
        self.assertTrue(mock_remove.called)

    @patch('src.infrastructure.storage.data_storage.os.makedirs')
    @patch('src.infrastructure.storage.data_storage.os.path.exists')
    @patch('src.infrastructure.storage.data_storage.os.remove')
    def test_clear_all_data_no_files(self, mock_remove, mock_exists, mock_makedirs):
        """Testa quando nenhum arquivo existe"""
        from src.infrastructure.storage.data_storage import DataStorage

        mock_exists.return_value = False

        DataStorage.clear_all_data()

        # Verifica se makedirs foi chamado
        mock_makedirs.assert_called()
        # Verifica se remove não foi chamado
        mock_remove.assert_not_called()

    @patch('src.infrastructure.storage.data_storage.os.makedirs')
    @patch('src.infrastructure.storage.data_storage.os.path.exists')
    @patch('src.infrastructure.storage.data_storage.os.remove')
    def test_clear_all_data_exception_handling(self, mock_remove, mock_exists, mock_makedirs):
        """Testa tratamento de exceções"""
        from src.infrastructure.storage.data_storage import DataStorage

        mock_exists.return_value = True
        mock_remove.side_effect = Exception("Permission denied")

        # Não deve lançar exceção
        try:
            DataStorage.clear_all_data()
        except Exception:
            self.fail("DataStorage.clear_all_data() lançou exceção inesperada")


if __name__ == '__main__':
    unittest.main()
