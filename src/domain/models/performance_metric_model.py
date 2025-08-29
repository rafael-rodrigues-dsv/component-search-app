"""
Modelo para métricas de performance
"""
from dataclasses import dataclass


@dataclass
class PerformanceMetricModel:
    """Modelo para uma métrica de performance individual"""
    operation: str
    duration: float
    success: bool
    timestamp: float