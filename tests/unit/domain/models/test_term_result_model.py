"""
Testes unitários para TermResultModel
"""
import unittest
import sys
import os

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src.domain.models.term_result_model import TermResultModel


class TestTermResultModel(unittest.TestCase):
    """Testes para TermResultModel"""
    
    def test_term_result_creation_with_defaults(self):
        """Testa criação com valores padrão"""
        result = TermResultModel(
            saved_count=5,
            processed_count=10,
            success=True,
            term_query="elevadores SP"
        )
        
        self.assertEqual(result.saved_count, 5)
        self.assertEqual(result.processed_count, 10)
        self.assertTrue(result.success)
        self.assertEqual(result.term_query, "elevadores SP")
        self.assertEqual(result.errors, [])
    
    def test_term_result_creation_with_errors(self):
        """Testa criação com lista de erros"""
        errors = ["Erro 1", "Erro 2"]
        result = TermResultModel(
            saved_count=0,
            processed_count=5,
            success=False,
            term_query="elevadores RJ",
            errors=errors
        )
        
        self.assertEqual(result.saved_count, 0)
        self.assertEqual(result.processed_count, 5)
        self.assertFalse(result.success)
        self.assertEqual(result.term_query, "elevadores RJ")
        self.assertEqual(result.errors, errors)
    
    def test_term_result_post_init_none_errors(self):
        """Testa __post_init__ quando errors é None"""
        result = TermResultModel(
            saved_count=3,
            processed_count=8,
            success=True,
            term_query="manutenção elevadores",
            errors=None
        )
        
        self.assertEqual(result.errors, [])
    
    def test_term_result_success_scenario(self):
        """Testa cenário de sucesso"""
        result = TermResultModel(
            saved_count=15,
            processed_count=20,
            success=True,
            term_query="instalação elevadores"
        )
        
        self.assertGreater(result.saved_count, 0)
        self.assertGreaterEqual(result.processed_count, result.saved_count)
        self.assertTrue(result.success)
        self.assertIsInstance(result.term_query, str)
        self.assertIsInstance(result.errors, list)
    
    def test_term_result_failure_scenario(self):
        """Testa cenário de falha"""
        result = TermResultModel(
            saved_count=0,
            processed_count=0,
            success=False,
            term_query="termo inválido",
            errors=["Busca falhou", "Timeout"]
        )
        
        self.assertEqual(result.saved_count, 0)
        self.assertEqual(result.processed_count, 0)
        self.assertFalse(result.success)
        self.assertEqual(len(result.errors), 2)


if __name__ == '__main__':
    unittest.main()