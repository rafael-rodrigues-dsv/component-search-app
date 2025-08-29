"""
Testes unitários para CollectionResultModel
"""
import unittest
import sys
import os

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src.domain.models.collection_result_model import CollectionResultModel
from src.domain.models.collection_stats_model import CollectionStatsModel


class TestCollectionResultModel(unittest.TestCase):
    """Testes para CollectionResultModel"""
    
    def test_collection_result_creation_success(self):
        """Testa criação de resultado bem-sucedido"""
        stats = CollectionStatsModel(
            total_saved=15,
            total_processed=30,
            terms_completed=5,
            terms_failed=0
        )
        
        result = CollectionResultModel(
            success=True,
            stats=stats,
            duration_seconds=120.5,
            message="Coleta concluída com sucesso"
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.stats, stats)
        self.assertEqual(result.duration_seconds, 120.5)
        self.assertEqual(result.message, "Coleta concluída com sucesso")
    
    def test_collection_result_creation_failure(self):
        """Testa criação de resultado com falha"""
        stats = CollectionStatsModel(
            total_saved=5,
            total_processed=10,
            terms_completed=2,
            terms_failed=3
        )
        
        result = CollectionResultModel(
            success=False,
            stats=stats,
            duration_seconds=45.2,
            message="Coleta falhou parcialmente"
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.stats, stats)
        self.assertEqual(result.duration_seconds, 45.2)
        self.assertEqual(result.message, "Coleta falhou parcialmente")
    
    def test_collection_result_stats_access(self):
        """Testa acesso às estatísticas através do resultado"""
        stats = CollectionStatsModel(
            total_saved=25,
            total_processed=50,
            terms_completed=10,
            terms_failed=2,
            start_time=1234567890.0
        )
        
        result = CollectionResultModel(
            success=True,
            stats=stats,
            duration_seconds=300.0,
            message="Processamento completo"
        )
        
        # Testa acesso direto às estatísticas
        self.assertEqual(result.stats.total_saved, 25)
        self.assertEqual(result.stats.total_processed, 50)
        self.assertEqual(result.stats.terms_completed, 10)
        self.assertEqual(result.stats.terms_failed, 2)
        self.assertEqual(result.stats.start_time, 1234567890.0)
    
    def test_collection_result_zero_duration(self):
        """Testa resultado com duração zero"""
        stats = CollectionStatsModel()
        
        result = CollectionResultModel(
            success=True,
            stats=stats,
            duration_seconds=0.0,
            message="Processamento instantâneo"
        )
        
        self.assertEqual(result.duration_seconds, 0.0)
        self.assertTrue(result.success)
    
    def test_collection_result_empty_message(self):
        """Testa resultado com mensagem vazia"""
        stats = CollectionStatsModel()
        
        result = CollectionResultModel(
            success=False,
            stats=stats,
            duration_seconds=10.5,
            message=""
        )
        
        self.assertEqual(result.message, "")
        self.assertFalse(result.success)
    
    def test_collection_result_types(self):
        """Testa tipos dos campos do resultado"""
        stats = CollectionStatsModel()
        
        result = CollectionResultModel(
            success=True,
            stats=stats,
            duration_seconds=60.0,
            message="Teste de tipos"
        )
        
        self.assertIsInstance(result.success, bool)
        self.assertIsInstance(result.stats, CollectionStatsModel)
        self.assertIsInstance(result.duration_seconds, float)
        self.assertIsInstance(result.message, str)


if __name__ == '__main__':
    unittest.main()