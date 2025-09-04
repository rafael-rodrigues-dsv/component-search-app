"""
Testes unitários para PerformanceTracker
"""
import time
import unittest
from unittest.mock import patch

from src.infrastructure.metrics.performance_tracker import PerformanceTracker


class TestPerformanceTracker(unittest.TestCase):
    """Testes para PerformanceTracker"""

    def setUp(self):
        """Setup para cada teste"""
        self.tracker = PerformanceTracker()

    def test_tracker_initialization(self):
        """Testa inicialização do tracker"""
        self.assertEqual(len(self.tracker.metrics), 0)
        self.assertIsInstance(self.tracker.metrics, list)

    def test_track_operation_success(self):
        """Testa rastreamento de operação bem-sucedida"""
        with self.tracker.track_operation("test_operation"):
            time.sleep(0.1)

        self.assertEqual(len(self.tracker.metrics), 1)
        metric = self.tracker.metrics[0]
        self.assertEqual(metric.operation, "test_operation")
        self.assertGreater(metric.duration, 0.1)
        self.assertTrue(metric.success)

    def test_track_operation_failure(self):
        """Testa rastreamento de operação com falha"""
        with self.assertRaises(ValueError):
            with self.tracker.track_operation("failing_operation"):
                raise ValueError("Test error")

        self.assertEqual(len(self.tracker.metrics), 1)
        metric = self.tracker.metrics[0]
        self.assertEqual(metric.operation, "failing_operation")
        self.assertFalse(metric.success)

    def test_add_metric_manually(self):
        """Testa adição manual de métrica"""
        self.tracker.add_metric("manual_operation", 1.5, True)

        self.assertEqual(len(self.tracker.metrics), 1)
        metric = self.tracker.metrics[0]
        self.assertEqual(metric.operation, "manual_operation")
        self.assertEqual(metric.duration, 1.5)
        self.assertTrue(metric.success)

    def test_add_metric_failure(self):
        """Testa adição manual de métrica com falha"""
        self.tracker.add_metric("failed_operation", 0.5, False)

        metric = self.tracker.metrics[0]
        self.assertFalse(metric.success)

    def test_get_stats_empty(self):
        """Testa estatísticas com tracker vazio"""
        stats = self.tracker.get_stats()
        self.assertEqual(stats, {})

    def test_get_stats_with_metrics(self):
        """Testa estatísticas com métricas"""
        self.tracker.add_metric("op1", 1.0, True)
        self.tracker.add_metric("op2", 2.0, True)
        self.tracker.add_metric("op3", 0.5, False)

        stats = self.tracker.get_stats()

        self.assertEqual(stats["avg_duration"], 1.5)  # (1.0 + 2.0) / 2
        self.assertEqual(stats["min_duration"], 1.0)
        self.assertEqual(stats["max_duration"], 2.0)
        self.assertEqual(stats["total_operations"], 3)
        self.assertEqual(stats["successful_operations"], 2)
        self.assertAlmostEqual(stats["success_rate"], 2 / 3, places=2)

    def test_get_stats_all_failures(self):
        """Testa estatísticas com todas as operações falhando"""
        self.tracker.add_metric("fail1", 1.0, False)
        self.tracker.add_metric("fail2", 2.0, False)

        stats = self.tracker.get_stats()

        self.assertEqual(stats["total_operations"], 2)
        self.assertEqual(stats["success_rate"], 0.0)
        self.assertNotIn("avg_duration", stats)

    def test_get_stats_with_filter(self):
        """Testa estatísticas com filtro"""
        self.tracker.add_metric("search_operation", 1.0, True)
        self.tracker.add_metric("extract_operation", 2.0, True)
        self.tracker.add_metric("search_another", 1.5, True)

        stats = self.tracker.get_stats("search")

        self.assertEqual(stats["total_operations"], 2)
        self.assertEqual(stats["avg_duration"], 1.25)  # (1.0 + 1.5) / 2

    def test_clear_metrics(self):
        """Testa limpeza de métricas"""
        self.tracker.add_metric("test", 1.0, True)
        self.assertEqual(len(self.tracker.metrics), 1)

        self.tracker.clear_metrics()
        self.assertEqual(len(self.tracker.metrics), 0)

    def test_get_recent_metrics(self):
        """Testa obtenção de métricas recentes"""
        # Adiciona métrica antiga (simulada)
        with patch('time.time', return_value=1000):
            self.tracker.add_metric("old_operation", 1.0, True)

        # Adiciona métrica recente
        with patch('time.time', return_value=7200):  # 2 horas depois (1000 + 3600*2)
            self.tracker.add_metric("recent_operation", 2.0, True)

        # Busca métricas da última hora (cutoff = 7200 - 3600 = 3600)
        with patch('time.time', return_value=7200):
            recent = self.tracker.get_recent_metrics(hours=1)

        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0].operation, "recent_operation")

    def test_multiple_operations_tracking(self):
        """Testa rastreamento de múltiplas operações"""
        with self.tracker.track_operation("op1"):
            time.sleep(0.05)

        with self.tracker.track_operation("op2"):
            time.sleep(0.05)

        self.assertEqual(len(self.tracker.metrics), 2)
        self.assertEqual(self.tracker.metrics[0].operation, "op1")
        self.assertEqual(self.tracker.metrics[1].operation, "op2")

    def test_nested_operations_tracking(self):
        """Testa rastreamento de operações aninhadas"""
        with self.tracker.track_operation("outer"):
            with self.tracker.track_operation("inner"):
                time.sleep(0.05)
            time.sleep(0.05)

        self.assertEqual(len(self.tracker.metrics), 2)
        # Inner deve ser mais rápida que outer
        inner_duration = next(m.duration for m in self.tracker.metrics if m.operation == "inner")
        outer_duration = next(m.duration for m in self.tracker.metrics if m.operation == "outer")
        self.assertGreater(outer_duration, inner_duration)


if __name__ == '__main__':
    unittest.main()
