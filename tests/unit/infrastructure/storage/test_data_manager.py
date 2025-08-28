"""
Testes unitários para DataManager
"""
import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src.infrastructure.storage.data_manager import DataManager


class TestDataManager(unittest.TestCase):
    """Testes para DataManager"""
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('os.remove')
    def test_clear_all_data_all_files_exist(self, mock_remove, mock_exists, mock_makedirs):
        """Testa limpeza quando todos os arquivos existem"""
        mock_exists.return_value = True
        
        with patch.dict('sys.modules', {'config.settings': MagicMock(
            DATA_DIR='test_data',
            VISITED_JSON='test_data/visited.json',
            SEEN_EMAILS_JSON='test_data/emails.json',
            OUTPUT_XLSX='output/empresas.xlsx'
        )}):
            DataManager.clear_all_data()
        
        mock_makedirs.assert_called_once_with('test_data', exist_ok=True)
        self.assertEqual(mock_remove.call_count, 3)
        mock_remove.assert_any_call('test_data/visited.json')
        mock_remove.assert_any_call('test_data/emails.json')
        mock_remove.assert_any_call('output/empresas.xlsx')
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('os.remove')
    def test_clear_all_data_no_files_exist(self, mock_remove, mock_exists, mock_makedirs):
        """Testa limpeza quando nenhum arquivo existe"""
        mock_exists.return_value = False
        
        with patch.dict('sys.modules', {'config.settings': MagicMock(
            DATA_DIR='test_data',
            VISITED_JSON='test_data/visited.json',
            SEEN_EMAILS_JSON='test_data/emails.json',
            OUTPUT_XLSX='output/empresas.xlsx'
        )}):
            DataManager.clear_all_data()
        
        mock_makedirs.assert_called_once_with('test_data', exist_ok=True)
        mock_remove.assert_not_called()
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('os.remove')
    def test_clear_all_data_some_files_exist(self, mock_remove, mock_exists, mock_makedirs):
        """Testa limpeza quando apenas alguns arquivos existem"""
        def exists_side_effect(path):
            return path in ['test_data/visited.json', 'output/empresas.xlsx']
        
        mock_exists.side_effect = exists_side_effect
        
        with patch.dict('sys.modules', {'config.settings': MagicMock(
            DATA_DIR='test_data',
            VISITED_JSON='test_data/visited.json',
            SEEN_EMAILS_JSON='test_data/emails.json',
            OUTPUT_XLSX='output/empresas.xlsx'
        )}):
            DataManager.clear_all_data()
        
        mock_makedirs.assert_called_once_with('test_data', exist_ok=True)
        self.assertEqual(mock_remove.call_count, 2)
        mock_remove.assert_any_call('test_data/visited.json')
        mock_remove.assert_any_call('output/empresas.xlsx')
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('os.remove')
    def test_clear_all_data_remove_exception(self, mock_remove, mock_exists, mock_makedirs):
        """Testa tratamento de exceção durante remoção"""
        mock_exists.return_value = True
        mock_remove.side_effect = [None, Exception("Permission denied"), None]
        
        with patch.dict('sys.modules', {'config.settings': MagicMock(
            DATA_DIR='test_data',
            VISITED_JSON='test_data/visited.json',
            SEEN_EMAILS_JSON='test_data/emails.json',
            OUTPUT_XLSX='output/empresas.xlsx'
        )}):
            # Não deve lançar exceção
            DataManager.clear_all_data()
        
        mock_makedirs.assert_called_once_with('test_data', exist_ok=True)
        self.assertEqual(mock_remove.call_count, 3)
    
    @patch('os.makedirs')
    def test_clear_all_data_makedirs_exception(self, mock_makedirs):
        """Testa exceção durante criação de diretório"""
        mock_makedirs.side_effect = Exception("Cannot create directory")
        
        with patch.dict('sys.modules', {'config.settings': MagicMock(
            DATA_DIR='test_data',
            VISITED_JSON='test_data/visited.json',
            SEEN_EMAILS_JSON='test_data/emails.json',
            OUTPUT_XLSX='output/empresas.xlsx'
        )}):
            with self.assertRaises(Exception):
                DataManager.clear_all_data()
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('os.remove')
    def test_clear_all_data_empty_paths(self, mock_remove, mock_exists, mock_makedirs):
        """Testa com caminhos vazios"""
        mock_exists.return_value = False
        
        with patch.dict('sys.modules', {'config.settings': MagicMock(
            DATA_DIR='',
            VISITED_JSON='',
            SEEN_EMAILS_JSON='',
            OUTPUT_XLSX=''
        )}):
            DataManager.clear_all_data()
        
        mock_makedirs.assert_called_once_with('', exist_ok=True)
        mock_remove.assert_not_called()
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    @patch('os.remove')
    def test_clear_all_data_multiple_calls(self, mock_remove, mock_exists, mock_makedirs):
        """Testa múltiplas chamadas consecutivas"""
        mock_exists.return_value = True
        
        with patch.dict('sys.modules', {'config.settings': MagicMock(
            DATA_DIR='test_data',
            VISITED_JSON='test_data/visited.json',
            SEEN_EMAILS_JSON='test_data/emails.json',
            OUTPUT_XLSX='output/empresas.xlsx'
        )}):
            # Primeira chamada
            DataManager.clear_all_data()
            
            # Segunda chamada
            DataManager.clear_all_data()
        
        # Deve ter sido chamado duas vezes
        self.assertEqual(mock_makedirs.call_count, 2)
        self.assertEqual(mock_remove.call_count, 6)  # 3 arquivos x 2 chamadas


if __name__ == '__main__':
    unittest.main()