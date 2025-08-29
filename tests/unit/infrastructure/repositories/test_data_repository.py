"""
Testes unitários simplificados para DataRepository
"""
import unittest
import sys
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

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
    
    def tearDown(self):
        """Cleanup após cada teste"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_json_repository_creation(self):
        """Testa criação do repositório JSON"""
        repo = JsonRepository(self.visited_path, self.emails_path)
        
        self.assertEqual(repo.visited_path, self.visited_path)
        self.assertEqual(repo.emails_path, self.emails_path)
        self.assertTrue(os.path.exists(self.temp_dir))
    
    def test_load_visited_domains_empty(self):
        """Testa carregamento de domínios quando arquivo não existe"""
        repo = JsonRepository(self.visited_path, self.emails_path)
        
        result = repo.load_visited_domains()
        
        self.assertEqual(result, {})
    
    def test_load_seen_emails_empty(self):
        """Testa carregamento de emails quando arquivo não existe"""
        repo = JsonRepository(self.visited_path, self.emails_path)
        
        result = repo.load_seen_emails()
        
        self.assertEqual(result, set())
    
    def test_save_and_load_visited_domains(self):
        """Testa salvamento e carregamento de domínios"""
        repo = JsonRepository(self.visited_path, self.emails_path)
        
        test_data = {"example.com": True, "test.com": True}
        repo.save_visited_domains(test_data)
        
        loaded_data = repo.load_visited_domains()
        self.assertEqual(loaded_data, test_data)
    
    def test_save_and_load_seen_emails(self):
        """Testa salvamento e carregamento de emails"""
        repo = JsonRepository(self.visited_path, self.emails_path)
        
        test_emails = {"test1@example.com", "test2@example.com"}
        repo.save_seen_emails(test_emails)
        
        loaded_emails = repo.load_seen_emails()
        self.assertEqual(loaded_emails, test_emails)


class TestExcelRepository(unittest.TestCase):
    """Testes para ExcelRepository"""
    
    def setUp(self):
        """Setup para cada teste"""
        self.temp_dir = tempfile.mkdtemp()
        self.excel_path = os.path.join(self.temp_dir, "test.xlsx")
    
    def tearDown(self):
        """Cleanup após cada teste"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.infrastructure.repositories.data_repository.Workbook')
    @patch('os.path.exists')
    def test_excel_repository_creation(self, mock_exists, mock_workbook):
        """Testa criação do repositório Excel"""
        mock_exists.return_value = False
        mock_wb = MagicMock()
        mock_workbook.return_value = mock_wb
        
        repo = ExcelRepository(self.excel_path)
        
        self.assertEqual(repo.file_path, self.excel_path)
    
    @patch('src.infrastructure.repositories.data_repository.load_workbook')
    @patch('os.path.exists')
    def test_save_company_with_emails(self, mock_exists, mock_load_workbook):
        """Testa salvamento de empresa com emails"""
        mock_exists.return_value = True
        mock_wb = MagicMock()
        mock_load_workbook.return_value = mock_wb
        
        repo = ExcelRepository(self.excel_path)
        
        company = CompanyModel(
            name="Test Company",
            emails="test@example.com;",
            domain="example.com",
            url="https://example.com"
        )
        
        # Não deve lançar exceção
        try:
            repo.save_company(company)
        except Exception as e:
            self.fail(f"save_company() lançou exceção: {e}")
    
    @patch('src.infrastructure.repositories.data_repository.load_workbook')
    @patch('os.path.exists')
    def test_save_company_without_emails(self, mock_exists, mock_load_workbook):
        """Testa que não salva empresa sem emails"""
        mock_exists.return_value = True
        
        repo = ExcelRepository(self.excel_path)
        
        company = CompanyModel(
            name="Test Company",
            emails="",
            domain="example.com",
            url="https://example.com"
        )
        
        # Não deve chamar load_workbook
        repo.save_company(company)
        mock_load_workbook.assert_not_called()


if __name__ == '__main__':
    unittest.main()