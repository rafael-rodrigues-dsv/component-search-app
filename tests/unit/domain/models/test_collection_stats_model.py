"""
Testes unitários para CollectionStatsModel
"""
import os
import sys
import unittest

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from src.domain.models.collection_stats_model import CollectionStatsModel
from src.domain.models.term_result_model import TermResultModel


class TestCollectionStatsModel(unittest.TestCase):
    """Testes para CollectionStatsModel"""

    def test_collection_stats_creation_with_defaults(self):
        """Testa criação com valores padrão"""
        stats = CollectionStatsModel()

        self.assertEqual(stats.total_saved, 0)
        self.assertEqual(stats.total_processed, 0)
        self.assertEqual(stats.terms_completed, 0)
        self.assertEqual(stats.terms_failed, 0)
        self.assertEqual(stats.start_time, 0.0)

    def test_collection_stats_creation_with_values(self):
        """Testa criação com valores específicos"""
        stats = CollectionStatsModel(
            total_saved=10,
            total_processed=25,
            terms_completed=5,
            terms_failed=1,
            start_time=1234567890.0
        )

        self.assertEqual(stats.total_saved, 10)
        self.assertEqual(stats.total_processed, 25)
        self.assertEqual(stats.terms_completed, 5)
        self.assertEqual(stats.terms_failed, 1)
        self.assertEqual(stats.start_time, 1234567890.0)

    def test_update_with_successful_term_result(self):
        """Testa atualização com resultado bem-sucedido"""
        stats = CollectionStatsModel()
        term_result = TermResultModel(
            saved_count=5,
            processed_count=10,
            success=True,
            term_query="elevadores SP"
        )

        stats.update(term_result)

        self.assertEqual(stats.total_saved, 5)
        self.assertEqual(stats.total_processed, 10)
        self.assertEqual(stats.terms_completed, 1)
        self.assertEqual(stats.terms_failed, 0)

    def test_update_with_failed_term_result(self):
        """Testa atualização com resultado falhado"""
        stats = CollectionStatsModel()
        term_result = TermResultModel(
            saved_count=0,
            processed_count=3,
            success=False,
            term_query="termo inválido"
        )

        stats.update(term_result)

        self.assertEqual(stats.total_saved, 0)
        self.assertEqual(stats.total_processed, 3)
        self.assertEqual(stats.terms_completed, 1)
        self.assertEqual(stats.terms_failed, 1)

    def test_update_multiple_term_results(self):
        """Testa atualização com múltiplos resultados"""
        stats = CollectionStatsModel()

        # Primeiro resultado - sucesso
        result1 = TermResultModel(
            saved_count=3,
            processed_count=5,
            success=True,
            term_query="elevadores SP"
        )
        stats.update(result1)

        # Segundo resultado - falha
        result2 = TermResultModel(
            saved_count=0,
            processed_count=2,
            success=False,
            term_query="termo inválido"
        )
        stats.update(result2)

        # Terceiro resultado - sucesso
        result3 = TermResultModel(
            saved_count=7,
            processed_count=12,
            success=True,
            term_query="manutenção elevadores"
        )
        stats.update(result3)

        self.assertEqual(stats.total_saved, 10)  # 3 + 0 + 7
        self.assertEqual(stats.total_processed, 19)  # 5 + 2 + 12
        self.assertEqual(stats.terms_completed, 3)
        self.assertEqual(stats.terms_failed, 1)

    def test_update_preserves_other_fields(self):
        """Testa que update preserva outros campos"""
        start_time = 1234567890.0
        stats = CollectionStatsModel(start_time=start_time)

        term_result = TermResultModel(
            saved_count=2,
            processed_count=4,
            success=True,
            term_query="test"
        )

        stats.update(term_result)

        self.assertEqual(stats.start_time, start_time)  # Deve ser preservado


if __name__ == '__main__':
    unittest.main()
