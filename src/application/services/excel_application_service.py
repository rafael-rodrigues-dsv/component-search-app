"""
Serviço de aplicação para exportação de Excel
"""
from pathlib import Path

from src.application.services.database_service import DatabaseService
from src.infrastructure.logging.structured_logger import StructuredLogger


class ExcelApplicationService:
    """Serviço de aplicação para geração de planilhas Excel"""

    def __init__(self):
        self.db_service = DatabaseService()
        self.logger = StructuredLogger("excel_export")

    def export_excel(self, custom_path: str = None) -> dict:
        """
        Exporta dados para Excel
        
        Returns:
            dict: {'success': bool, 'count': int, 'path': str, 'message': str}
        """
        try:
            self.logger.info("Iniciando exportação Excel")

            # Verificar se há dados para exportar
            stats = self.db_service.get_statistics()
            if not stats or stats.get('empresas_coletadas', 0) == 0:
                return {
                    'success': False,
                    'count': 0,
                    'path': None,
                    'message': 'Nenhuma empresa com dados coletados encontrada'
                }

            # Definir caminho do arquivo
            if custom_path:
                excel_path = Path(custom_path)
            else:
                excel_path = Path("output") / "empresas.xlsx"

            # Criar diretório se não existir
            excel_path.parent.mkdir(exist_ok=True)

            # Exportar dados
            success, count = self.db_service.export_to_excel(str(excel_path))

            if success:
                self.logger.info("Excel exportado com sucesso",
                                 count=count,
                                 path=str(excel_path))
                return {
                    'success': True,
                    'count': count,
                    'path': str(excel_path),
                    'message': f'Excel gerado com {count} registros'
                }
            else:
                self.logger.error("Falha na exportação Excel")
                return {
                    'success': False,
                    'count': 0,
                    'path': None,
                    'message': 'Erro interno na exportação'
                }

        except Exception as e:
            self.logger.error("Erro na exportação Excel", error=str(e))
            return {
                'success': False,
                'count': 0,
                'path': None,
                'message': f'Erro: {str(e)}'
            }

    def get_export_stats(self) -> dict:
        """
        Obtém estatísticas para exportação
        
        Returns:
            dict: Estatísticas dos dados disponíveis para exportação
        """
        try:
            stats = self.db_service.get_statistics()

            if not stats:
                return {
                    'empresas_disponiveis': 0,
                    'emails_disponiveis': 0,
                    'telefones_disponiveis': 0,
                    'pode_exportar': False
                }

            return {
                'empresas_disponiveis': stats.get('empresas_coletadas', 0),
                'emails_disponiveis': stats.get('emails_total', 0),
                'telefones_disponiveis': stats.get('telefones_total', 0),
                'pode_exportar': stats.get('empresas_coletadas', 0) > 0
            }

        except Exception as e:
            self.logger.error("Erro ao obter estatísticas de exportação", error=str(e))
            return {
                'empresas_disponiveis': 0,
                'emails_disponiveis': 0,
                'telefones_disponiveis': 0,
                'pode_exportar': False
            }
