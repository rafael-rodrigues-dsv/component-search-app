"""
Modelo para estatísticas da coleta completa
"""
from dataclasses import dataclass
from .term_result_model import TermResultModel


@dataclass
class CollectionStatsModel:
    """Estatísticas da coleta completa"""
    total_saved: int = 0
    total_processed: int = 0
    terms_completed: int = 0
    terms_failed: int = 0
    start_time: float = 0.0
    
    def update(self, term_result: TermResultModel) -> None:
        """Atualiza estatísticas com resultado de um termo"""
        self.total_saved += term_result.saved_count
        self.total_processed += term_result.processed_count
        self.terms_completed += 1
        if not term_result.success:
            self.terms_failed += 1