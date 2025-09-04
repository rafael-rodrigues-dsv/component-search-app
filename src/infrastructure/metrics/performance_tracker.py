"""
Rastreador de métricas de performance
"""
import time
from contextlib import contextmanager
from typing import Dict, List, Optional

from src.domain.models.performance_metric_model import PerformanceMetricModel


class PerformanceTracker:
    """Rastreador de métricas de performance com contexto"""

    def __init__(self):
        self.metrics: List[PerformanceMetricModel] = []

    @contextmanager
    def track_operation(self, operation: str):
        """Context manager para rastrear operação"""
        start_time = time.time()
        success = True
        try:
            yield
        except Exception:
            success = False
            raise
        finally:
            duration = time.time() - start_time
            self.metrics.append(PerformanceMetricModel(
                operation=operation,
                duration=duration,
                success=success,
                timestamp=start_time
            ))

    def add_metric(self, operation: str, duration: float, success: bool = True) -> None:
        """Adiciona métrica manualmente"""
        self.metrics.append(PerformanceMetricModel(
            operation=operation,
            duration=duration,
            success=success,
            timestamp=time.time()
        ))

    def get_stats(self, operation_filter: Optional[str] = None) -> Dict[str, float]:
        """Obtém estatísticas das métricas"""
        filtered_metrics = self.metrics
        if operation_filter:
            filtered_metrics = [m for m in self.metrics if operation_filter in m.operation]

        if not filtered_metrics:
            return {}

        successful_metrics = [m for m in filtered_metrics if m.success]
        durations = [m.duration for m in successful_metrics]

        if not durations:
            return {
                "total_operations": len(filtered_metrics),
                "success_rate": 0.0
            }

        return {
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "total_operations": len(filtered_metrics),
            "successful_operations": len(successful_metrics),
            "success_rate": len(successful_metrics) / len(filtered_metrics)
        }

    def clear_metrics(self) -> None:
        """Limpa todas as métricas"""
        self.metrics.clear()

    def get_recent_metrics(self, hours: int = 1) -> List[PerformanceMetricModel]:
        """Obtém métricas das últimas N horas"""
        cutoff_time = time.time() - (hours * 3600)
        return [m for m in self.metrics if m.timestamp >= cutoff_time]
