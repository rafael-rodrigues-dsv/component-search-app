"""
Fast Search Single Thread Service - Sistema legado/rápido
Processamento sequencial sem classificação inteligente de sites
"""
from typing import Dict, Callable, Optional

from src.infrastructure.config.config_manager import ConfigManager
from src.infrastructure.logging.structured_logger import StructuredLogger


class FastSearchSingleThreadService:
    """
    Single-thread service para Fast Search (legado/rápido)

    Características:
    - Processamento sequencial (um termo por vez)
    - Usa scrapers Fast Search
    - Sem classificação de sites
    - Interface compatível com sistema existente
    """

    def __init__(self):
        self.config = ConfigManager()
        self.logger = StructuredLogger("fast_search_single_thread")

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
        Executa coleta single-thread com Fast Search

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
            f"Iniciando Fast Search (single-thread)",
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
                search_mode='FAST',  # 🆕 Força Fast Search
                progress_callback=progress_callback,
                should_stop_callback=should_stop_callback,
                db_lock=db_lock
            )

            return result

        except Exception as e:
            self.logger.error(f"Erro na coleta Fast Search: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
