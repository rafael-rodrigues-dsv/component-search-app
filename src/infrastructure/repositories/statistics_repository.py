"""
Repository for aggregated statistics (used by dashboard/service layers)
"""
from typing import Dict
from src.infrastructure.repositories.access_repository import AccessRepository

class StatisticsRepository:
    def __init__(self):
        self._access = AccessRepository()

    def get_processing_statistics(self) -> Dict[str, int]:
        """Return aggregated processing statistics used by the dashboard."""
        try:
            conn = self._access._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM TB_TERMOS_BUSCA")
            total_termos = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM TB_TERMOS_BUSCA WHERE STATUS_PROCESSAMENTO = 'CONCLUIDO'")
            termos_concluidos = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM TB_TERMOS_BUSCA WHERE STATUS_PROCESSAMENTO = 'PENDENTE'")
            termos_pendentes = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM TB_EMPRESAS")
            total_empresas = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM TB_EMPRESAS WHERE STATUS_COLETA = 'COLETADO'")
            empresas_coletadas = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM TB_EMAILS")
            total_emails = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM TB_TELEFONES")
            total_telefones = cursor.fetchone()[0]
            try:
                cursor.close()
            except Exception:
                pass
            return {
                'termos_total': total_termos,
                'termos_concluidos': termos_concluidos,
                'termos_pendentes': termos_pendentes,
                'empresas_total': total_empresas,
                'empresas_coletadas': empresas_coletadas,
                'emails_total': total_emails,
                'telefones_total': total_telefones,
                'progresso_pct': round((termos_concluidos / total_termos * 100), 1) if total_termos > 0 else 0
            }
        except Exception:
            return {
                'termos_total': 0,
                'termos_concluidos': 0,
                'termos_pendentes': 0,
                'empresas_total': 0,
                'empresas_coletadas': 0,
                'emails_total': 0,
                'telefones_total': 0,
                'progresso_pct': 0
            }
