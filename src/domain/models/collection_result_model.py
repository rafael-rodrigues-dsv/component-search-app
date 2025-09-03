"""
Modelo para resultado final da coleta
"""
from dataclasses import dataclass
from .collection_stats_model import CollectionStatsModel


@dataclass
class CollectionResultModel:
    """Resultado final da coleta"""
    success: bool
    stats: CollectionStatsModel
    duration_seconds: float
    message: str
