"""
Deep Search Single Thread Service - Sistema inteligente
Processamento sequencial COM classificação inteligente de sites e extração avançada
"""
from typing import List, Dict, Callable, Optional

from src.infrastructure.config.config_manager import ConfigManager
from src.infrastructure.logging.structured_logger import StructuredLogger


class DeepSearchSingleThreadService:
    """
    Single-thread service para Deep Search (inteligente)

    Características:
    - Processamento sequencial (um termo por vez)
    - Usa Deep Search Scrapers (com classificação)
    - Classificação automática de sites
    - Extração inteligente
    """

    def __init__(self):
        self.config = ConfigManager()
        self.logger = StructuredLogger("deep_search_single_thread")

    def execute_collection(
        self,
        term: str,
        browser: str = 'CHROME',
        engine: str = 'GOOGLE',
        headless: bool = False,
        progress_callback: Optional[Callable] = None,
        should_stop_callback: Optional[Callable] = None,
        db_lock = None
    ) -> Dict:
        """
        Executa coleta single-thread com Deep Search

        Args:
            term: Termo de busca
            browser: Navegador (CHROME ou BRAVE)
            engine: Motor de busca (GOOGLE ou DUCKDUCKGO)
            headless: Se True, navegador invisível
            progress_callback: Callback para progresso (opcional)
            should_stop_callback: Callback para verificar parada (opcional)
            db_lock: Lock para operações no banco (opcional)

        Returns:
            Dict com resultado da coleta
        """
        self.logger.info(
            f"Iniciando Deep Search (single-thread)",
            term=term,
            browser=browser,
            engine=engine,
            headless=headless
        )

        try:
            # Usar CollectionExecutorService para executar a coleta
            from .collection_executor_service import CollectionExecutorService
            executor = CollectionExecutorService()

            result = executor.execute_collection_for_term(
                term=term,
                browser=browser,
                engine=engine,
                headless=headless,
                search_mode='DEEP',  # 🆕 Força Deep Search
                progress_callback=progress_callback,
                should_stop_callback=should_stop_callback,
                db_lock=db_lock
            )

            return result

        except Exception as e:
            self.logger.error(f"Erro na coleta Deep Search: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
