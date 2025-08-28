"""
Testes unitários para DataRepository
"""
import unittest
import sys
import os
import json
import tempfile
import shutil
from unittest.mock import patch, mock_open, MagicMock

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src.infrastructure.repositories.data_repository import JsonRepository, ExcelRepository
from src.domain.models.company_model import CompanyModel


class TestJsonRepository(unittest.TestCase):
    """Testes para JsonRepository"""
    
    def setUp(self):
        """Setup para cada teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.visited_path = os.path.join(self.temp_dir, "visited.json")
        self.emails_path = os.path.join(self.temp_dir, "emails.json")
        self.repo = JsonRepository(self.visited_path, self.emails_path)
    
    def tearDown(self):
        """Cleanup após cada teste"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_creates_data_directory(self):
        """Testa se o construtor cria o diretório de dados"""
        self.assertTrue(os.path.exists(self.temp_dir))
    
    def test_load_visited_domains_empty_file(self):
        """Testa carregamento quando arquivo não existe"""
        result = self.repo.load_visited_domains()
        self.assertEqual(result, {})
    
    def test_load_visited_domains_with_data(self):
        """Testa carregamento com dados existentes"""
        test_data = {"example.com": True, "test.com": True}
        with open(self.visited_path, "w", encoding="utf-8") as f:
            json.dump(test_data, f)
        
        result = self.repo.load_visited_domains()
        self.assertEqual(result, test_data)
    
    def test_save_visited_domains(self):
        """Testa salvamento de domínios visitados"""
        test_data = {"example.com": True, "test.com": True}
        
        self.repo.save_visited_domains(test_data)
        
        with open(self.visited_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, test_data)
    
    def test_load_seen_emails_empty_file(self):
        """Testa carregamento quando arquivo de emails não existe"""
        result = self.repo.load_seen_emails()
        self.assertEqual(result, set())
    
    def test_load_seen_emails_with_data(self):
        """Testa carregamento com emails existentes"""
        test_emails = ["test1@example.com", "test2@example.com"]
        with open(self.emails_path, "w", encoding="utf-8") as f:
            json.dump(test_emails, f)
        
        result = self.repo.load_seen_emails()
        self.assertEqual(result, set(test_emails))
    
    def test_save_seen_emails(self):
        """Testa salvamento de emails"""
        test_emails = {"test1@example.com", "test2@example.com"}
        
        self.repo.save_seen_emails(test_emails)
        
        with open(self.emails_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        
        self.assertEqual(set(saved_data), test_emails)
    
    @patch('builtins.open', side_effect=Exception("File error"))
    def test_load_json_exception(self, mock_open):
        """Testa tratamento de exceção no carregamento"""
        result = self.repo._load_json("invalid_path.json")
        self.assertIsNone(result)
    
    def test_load_json_invalid_json(self):
        """Testa carregamento de JSON inválido"""
        with open(self.visited_path, "w") as f:
            f.write("invalid json content")
        
        result = self.repo._load_json(self.visited_path)
        self.assertIsNone(result)
    
    def test_save_json_with_unicode(self):
        """Testa salvamento com caracteres unicode"""
        test_data = {"site.com.br": True, "elevadores-são-paulo.com": True}
        
        self.repo._save_json(self.visited_path, test_data)
        
        with open(self.visited_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, test_data)


class TestExcelRepository(unittest.TestCase):
    """Testes para ExcelRepository"""
    
    def setUp(self):
        """Setup para cada teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.excel_path = os.path.join(self.temp_dir, "test.xlsx")
        
    def tearDown(self):
        """Cleanup após cada teste"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('os.path.exists')
    @patch('openpyxl.Workbook')
    def test_init_creates_excel_file(self, mock_workbook, mock_exists):
        """Testa se o construtor cria arquivo Excel"""
        mock_exists.return_value = False  # Arquivo não existe
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws
        mock_workbook.return_value = mock_wb
        
        repo = ExcelRepository(self.excel_path)
        
        mock_workbook.assert_called_once()
        mock_wb.save.assert_called_once_with(self.excel_path)
    
    @patch('os.path.exists')
    @patch('openpyxl.Workbook')
    def test_ensure_excel_exists_creates_file(self, mock_workbook, mock_exists):
        """Testa criação de arquivo Excel quando não existe"""
        mock_exists.return_value = False
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.active = mock_ws
        mock_workbook.return_value = mock_wb
        
        repo = ExcelRepository(self.excel_path)
        
        # Verifica se o workbook foi criado
        mock_workbook.assert_called_once()
        mock_wb.save.assert_called_once_with(self.excel_path)
    
    @patch('os.path.exists')
    def test_ensure_excel_exists_file_already_exists(self, mock_exists):
        """Testa quando arquivo Excel já existe"""
        mock_exists.return_value = True
        
        with patch('openpyxl.Workbook') as mock_workbook:
            repo = ExcelRepository(self.excel_path)
            mock_workbook.assert_not_called()
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_ensure_output_dir_creates_directory(self, mock_exists, mock_makedirs):
        """Testa criação de diretório de saída"""
        mock_exists.return_value = False
        
        with patch('openpyxl.Workbook'):
            repo = ExcelRepository(self.excel_path)
        
        mock_makedirs.assert_called_once_with(self.temp_dir)
    
    @patch('os.makedirs')
    @patch('os.path.exists')
    def test_ensure_output_dir_already_exists(self, mock_exists, mock_makedirs):
        """Testa quando diretório já existe"""
        mock_exists.return_value = True
        
        with patch('openpyxl.Workbook'):
            repo = ExcelRepository(self.excel_path)
        
        mock_makedirs.assert_not_called()
    
    @patch('os.path.exists')
    @patch('openpyxl.load_workbook')
    @patch('openpyxl.Workbook')
    def test_save_company_success(self, mock_workbook, mock_load_workbook, mock_exists):
        """Testa salvamento bem-sucedido de empresa"""
        # Mock para inicialização
        mock_exists.return_value = True  # Arquivo já existe
        
        # Mock para salvamento
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.__getitem__.return_value = mock_ws
        mock_ws.max_row = 2
        mock_load_workbook.return_value = mock_wb
        
        repo = ExcelRepository(self.excel_path)
        
        company = CompanyModel(
            name="Test Company",
            emails="test@example.com;",
            domain="example.com",
            url="https://example.com",
            phone="(11) 99999-8888;"
        )
        
        repo.save_company(company)
        
        mock_load_workbook.assert_called_once_with(self.excel_path)
        mock_ws.append.assert_called_once_with([
            "https://example.com",
            "test@example.com;",
            "(11) 99999-8888;"
        ])
        mock_wb.save.assert_called_once_with(self.excel_path)
    
    @patch('os.path.exists')
    @patch('openpyxl.load_workbook')
    @patch('openpyxl.Workbook')
    def test_save_company_no_emails(self, mock_workbook, mock_load, mock_exists):
        """Testa que não salva empresa sem emails"""
        mock_exists.return_value = True
        
        repo = ExcelRepository(self.excel_path)
        
        company = CompanyModel(
            name="Test Company",
            emails="",
            domain="example.com",
            url="https://example.com"
        )
        
        repo.save_company(company)
        
        mock_load.assert_not_called()
    
    @patch('os.path.exists')
    @patch('openpyxl.load_workbook')
    @patch('openpyxl.Workbook')
    def test_save_company_exception_handling(self, mock_workbook, mock_load_workbook, mock_exists):
        """Testa tratamento de exceção durante salvamento"""
        mock_exists.return_value = True
        mock_load_workbook.side_effect = Exception("Excel error")
        
        repo = ExcelRepository(self.excel_path)
        
        company = CompanyModel(
            name="Test Company",
            emails="test@example.com;",
            domain="example.com",
            url="https://example.com"
        )
        
        # Não deve lançar exceção
        repo.save_company(company)
    
    @patch('os.path.exists')
    @patch('openpyxl.load_workbook')
    @patch('openpyxl.Workbook')
    def test_save_company_with_multiple_emails_and_phones(self, mock_workbook, mock_load_workbook, mock_exists):
        """Testa salvamento com múltiplos emails e telefones"""
        mock_exists.return_value = True
        
        mock_wb = MagicMock()
        mock_ws = MagicMock()
        mock_wb.__getitem__.return_value = mock_ws
        mock_ws.max_row = 2
        mock_load_workbook.return_value = mock_wb
        
        repo = ExcelRepository(self.excel_path)
        
        company = CompanyModel(
            name="Multi Contact Company",
            emails="email1@example.com;email2@example.com;",
            domain="example.com",
            url="https://example.com",
            phone="(11) 99999-8888;(11) 3333-4444;"
        )
        
        repo.save_company(company)
        
        mock_load_workbook.assert_called_once_with(self.excel_path)
        mock_ws.append.assert_called_once_with([
            "https://example.com",
            "email1@example.com;email2@example.com;",
            "(11) 99999-8888;(11) 3333-4444;"
        ])
        mock_wb.save.assert_called_once_with(self.excel_path)


if __name__ == '__main__':
    unittest.main()