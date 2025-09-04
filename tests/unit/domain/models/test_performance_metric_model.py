"""
Testes unitários para PerformanceMetricModel
"""
import time
import unittest

from src.domain.models.performance_metric_model import PerformanceMetricModel


class TestPerformanceMetricModel(unittest.TestCase):
    """Testes para PerformanceMetricModel"""

    def test_performance_metric_creation(self):
        """Testa criação do modelo"""
        timestamp = time.time()
        metric = PerformanceMetricModel(
            operation="test_operation",
            duration=1.5,
            success=True,
            timestamp=timestamp
        )

        self.assertEqual(metric.operation, "test_operation")
        self.assertEqual(metric.duration, 1.5)
        self.assertTrue(metric.success)
        self.assertEqual(metric.timestamp, timestamp)

    def test_performance_metric_failure_scenario(self):
        """Testa cenário de falha"""
        metric = PerformanceMetricModel(
            operation="failed_operation",
            duration=0.5,
            success=False,
            timestamp=time.time()
        )

        self.assertFalse(metric.success)
        self.assertEqual(metric.operation, "failed_operation")

    def test_performance_metric_types(self):
        """Testa tipos dos campos"""
        metric = PerformanceMetricModel("op", 1.0, True, 123.456)

        self.assertIsInstance(metric.operation, str)
        self.assertIsInstance(metric.duration, float)
        self.assertIsInstance(metric.success, bool)
        self.assertIsInstance(metric.timestamp, float)

    def test_performance_metric_zero_duration(self):
        """Testa duração zero"""
        metric = PerformanceMetricModel("instant_op", 0.0, True, time.time())

        self.assertEqual(metric.duration, 0.0)
        self.assertTrue(metric.success)

    def test_performance_metric_long_operation_name(self):
        """Testa nome de operação longo"""
        long_name = "very_long_operation_name_that_exceeds_normal_length"
        metric = PerformanceMetricModel(long_name, 2.5, True, time.time())

        self.assertEqual(metric.operation, long_name)


if __name__ == '__main__':
    unittest.main()
