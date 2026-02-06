"""
Company Search Router Service - Direcionador de coletas
Responsável apenas por direcionar para o service correto baseado nas escolhas do usuário
"""
from typing import Dict, Optional, Callable


class CompanySearchRouterService:
    """
    Router Service - Direciona para o service correto

    Decisões:
    - Processing Mode (SINGLE ou MULTI)
    - Search Mode (FAST ou DEEP)
    - Browser (CHROME ou BRAVE)
    - Engine (GOOGLE ou DUCKDUCKGO)
    - Headless (True ou False)
    """

    def __init__(self):
        pass

    def route_collection(
        self,
        processing_mode: str,  # 'SINGLE' ou 'MULTI'
        search_mode: str,  # 'FAST' ou 'DEEP'
        browser: str = 'CHROME',
        engine: str = 'GOOGLE',
        headless: bool = False,
        term: Optional[str] = None,  # Para SINGLE
        terms: Optional[list] = None,  # Para MULTI
        progress_callback: Optional[Callable] = None,
        should_stop_callback: Optional[Callable] = None,
        db_lock = None
    ) -> Dict:
        """
        Direciona a coleta para o service correto

        Args:
            processing_mode: 'SINGLE' ou 'MULTI'
            search_mode: 'FAST' ou 'DEEP'
            browser: Navegador
            engine: Motor de busca
            headless: Modo headless
            term: Termo único (para SINGLE)
            terms: Lista de termos (para MULTI)
            progress_callback: Callback de progresso
            should_stop_callback: Callback de parada
            db_lock: Lock do banco

        Returns:
            Dict com resultado da coleta
        """
        print(f"[ROUTER] Direcionando coleta: processing={processing_mode}, search={search_mode}, engine={engine}")

        # Decisão 1: SINGLE ou MULTI thread?
        if processing_mode == 'SINGLE':
            return self._route_single_thread(
                search_mode=search_mode,
                term=term,
                browser=browser,
                engine=engine,
                headless=headless,
                progress_callback=progress_callback,
                should_stop_callback=should_stop_callback,
                db_lock=db_lock
            )
        else:  # MULTI
            return self._route_multi_thread(
                search_mode=search_mode,
                terms=terms,
                browser=browser,
                engine=engine,
                headless=headless
            )

    def _route_single_thread(
        self,
        search_mode: str,
        term: str,
        browser: str,
        engine: str,
        headless: bool,
        progress_callback: Optional[Callable],
        should_stop_callback: Optional[Callable],
        db_lock
    ) -> Dict:
        """Direciona para single-thread service"""

        # Decisão 2: FAST ou DEEP search?
        if search_mode == 'FAST':
            print("[ROUTER] → FastSearchSingleThreadService")
            from src.infrastructure.scrapers.services.fast_search_single_thread_service import FastSearchSingleThreadService
            service = FastSearchSingleThreadService()
        else:  # DEEP
            print("[ROUTER] → DeepSearchSingleThreadService")
            from src.infrastructure.scrapers.services.deep_search_single_thread_service import DeepSearchSingleThreadService
            service = DeepSearchSingleThreadService()

        # Executar coleta
        return service.execute_collection(
            term=term,
            browser=browser,
            engine=engine,
            headless=headless,
            progress_callback=progress_callback,
            should_stop_callback=should_stop_callback,
            db_lock=db_lock
        )

    def _route_multi_thread(
        self,
        search_mode: str,
        terms: list,
        browser: str,
        engine: str,
        headless: bool
    ) -> Dict:
        """Direciona para multi-thread service"""

        # Decisão 2: FAST ou DEEP search?
        if search_mode == 'FAST':
            print("[ROUTER] → FastSearchMultiThreadService")
            from src.infrastructure.scrapers.services.fast_search_multi_thread_service import FastSearchMultiThreadService
            service = FastSearchMultiThreadService()

            # Fast Multi-Thread não tem o mesmo padrão de start_collection
            # Precisa adaptar para usar collect_mixed_parallel
            return {
                'success': False,
                'message': 'Fast Search Multi-Thread ainda não implementado completamente'
            }
        else:  # DEEP
            print("[ROUTER] → DeepSearchMultiThreadService")
            from src.infrastructure.scrapers.services.deep_search_multi_thread_service import DeepSearchMultiThreadService
            service = DeepSearchMultiThreadService()

            # Iniciar coleta multi-thread
            return service.start_collection(
                terms=terms,
                browser=browser,
                engine=engine,
                headless=headless
            )
