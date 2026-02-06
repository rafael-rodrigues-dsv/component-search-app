"""
Deep Search Multi-Thread Service - Sistema inteligente
Processamento paralelo COM classificação inteligente de sites e extração avançada
"""
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Dict, Callable

from src.domain.models.collection_thread_state import CollectionThreadState, CollectionState
from src.infrastructure.config.config_manager import ConfigManager


class DeepSearchMultiThreadService:
    """
    Multi-thread service para Deep Search (inteligente)

    Características:
    - Coordenação de múltiplas threads
    - Usa Deep Search Scrapers (com classificação)
    - Gerenciamento de fila e estado
    - Callbacks de progresso
    """

    def __init__(self):
        self.config = ConfigManager()
        self.state = CollectionState()
        self.state_lock = threading.Lock()
        self.db_lock = threading.Lock()  # Lock para operações no banco Access

        # Carregar configurações
        self.state.max_workers = self.config.get_config_value(
            'search.multi_threading.max_workers',
            10
        )
        self.queue_check_interval = self.config.get_config_value(
            'search.multi_threading.queue_check_interval',
            1.0
        )
        self.thread_timeout = self.config.get_config_value(
            'search.multi_threading.thread_timeout',
            3600
        )

        # Callback para atualizar UI (opcional)
        self.progress_callback: Optional[Callable] = None

    def set_progress_callback(self, callback: Callable):
        """Define callback para notificar progresso à UI"""
        self.progress_callback = callback

    def start_collection(self, terms: List[str], browser: str = 'CHROME', engine: str = 'GOOGLE', headless: bool = False) -> Dict:
        """
        Inicia coleta multi-thread com os termos fornecidos

        Args:
            terms: Lista de termos de busca para processar
            browser: Navegador a usar (CHROME ou BRAVE)
            engine: Motor de busca (GOOGLE ou DUCKDUCKGO)
            headless: Se True, executa navegador invisível

        Returns:
            Dict com status da operação
        """
        if not terms:
            return {
                'success': False,
                'message': 'Nenhum termo fornecido para processar'
            }

        if self.state.is_running:
            return {
                'success': False,
                'message': 'Já existe uma coleta em andamento'
            }

        # Inicializar estado
        with self.state_lock:
            self.state.is_running = True
            self.state.should_stop = False
            self.state.pending_terms = terms.copy()
            self.state.threads.clear()
            self.state.active_threads = 0

            # Armazenar configurações da UI
            self.state.browser = browser
            self.state.engine = engine
            self.state.headless = headless

        print(f"[MULTI-THREAD] Iniciando com: browser={browser}, engine={engine}, headless={headless}")

        # Calcular número real de threads que serão usadas
        actual_threads = min(self.state.max_workers, len(terms))

        # Iniciar processamento em background thread
        collection_thread = threading.Thread(
            target=self._run_collection_worker,
            args=(terms,),
            daemon=True
        )
        collection_thread.start()

        return {
            'success': True,
            'message': f'Coleta iniciada com {len(terms)} termos',
            'max_workers': self.state.max_workers,
            'terms_count': len(terms),
            'actual_threads': actual_threads  # Número real de threads que serão usadas
        }

    def _run_collection_worker(self, terms: List[str]):
        """
        Worker principal que gerencia o ThreadPoolExecutor
        Executa em background thread separada
        """
        try:
            # Criar ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=self.state.max_workers) as executor:
                # Submeter tarefas iniciais (até max_workers)
                futures = {}
                thread_counter = 0

                for i, term in enumerate(terms[:self.state.max_workers]):
                    future = executor.submit(
                        self._process_term_thread,
                        term,
                        thread_counter
                    )
                    futures[future] = (thread_counter, term)
                    thread_counter += 1

                # Termos restantes para adicionar conforme threads terminam
                remaining_terms = terms[self.state.max_workers:]
                remaining_index = 0

                print(f"[MULTI-THREAD] {len(futures)} threads iniciais criadas, {len(remaining_terms)} termos na fila")

                # Processar conforme threads terminam
                # Usar um set separado para rastrear todos os futures
                all_futures = set(futures.keys())

                while all_futures:
                    # Aguardar conclusão de qualquer future
                    done_futures = set()
                    for future in as_completed(all_futures):
                        done_futures.add(future)

                        thread_id, term = futures[future]

                        # Verificar resultado
                        try:
                            result = future.result(timeout=self.thread_timeout)

                            # Atualizar estado da thread
                            with self.state_lock:
                                if thread_id in self.state.threads:
                                    if result.get('success'):
                                        self.state.threads[thread_id].complete()
                                        self.state.threads[thread_id].companies_found = result.get('companies_found', 0)
                                    elif result.get('stopped'):
                                        self.state.threads[thread_id].stop()
                                    else:
                                        self.state.threads[thread_id].error(result.get('error', 'Erro desconhecido'))

                        except Exception as e:
                            # Marcar thread com erro
                            with self.state_lock:
                                if thread_id in self.state.threads:
                                    self.state.threads[thread_id].error(str(e))

                        # Se deve parar, cancelar futures restantes
                        if self.state.should_stop:
                            for f in all_futures:
                                if not f.done():
                                    f.cancel()
                            all_futures.clear()
                            break

                        # Se ainda há termos pendentes, adicionar à fila
                        if remaining_index < len(remaining_terms) and not self.state.should_stop:
                            next_term = remaining_terms[remaining_index]
                            remaining_index += 1

                            new_future = executor.submit(
                                self._process_term_thread,
                                next_term,
                                thread_counter
                            )
                            futures[new_future] = (thread_counter, next_term)
                            all_futures.add(new_future)  # Adicionar ao set de futures ativos
                            thread_counter += 1

                            print(f"[MULTI-THREAD] Thread concluída. Adicionando novo termo: {next_term} (total: {remaining_index}/{len(remaining_terms)} restantes)")

                        # Processar apenas o primeiro future completo e então verificar novos
                        break

                    # Remover futures concluídos do set
                    all_futures -= done_futures

        finally:
            # Finalizar coleta
            with self.state_lock:
                self.state.is_running = False
                self.state.active_threads = 0

            print(f"[MULTI-THREAD] Coleta finalizada. Total de termos processados: {thread_counter}")

            # Notificar UI
            if self.progress_callback:
                self.progress_callback('collection_finished', self.state.to_dict())

    def _process_term_thread(self, term: str, thread_id: int) -> Dict:
        """
        Processa um termo em uma thread individual usando Deep Search

        Args:
            term: Termo de busca
            thread_id: ID único da thread

        Returns:
            Dict com resultado do processamento
        """
        # Criar estado da thread
        thread_state = CollectionThreadState(
            thread_id=thread_id,
            term=term,
            status='pending'
        )

        # Registrar thread
        with self.state_lock:
            self.state.threads[thread_id] = thread_state
            self.state.active_threads += 1

        # Iniciar processamento
        thread_state.start()

        print(f"[THREAD-{thread_id}] Iniciando processamento do termo: {term}")

        # Notificar UI
        if self.progress_callback:
            self.progress_callback('thread_started', thread_state.to_dict())

        try:
            # Obter configurações da UI do estado global
            browser = self.state.browser
            engine = self.state.engine
            headless = self.state.headless

            print(f"[THREAD-{thread_id}] Aplicando configurações: browser={browser}, engine={engine}, headless={headless}")

            # Aplicar temporariamente a configuração headless no ConfigManager
            from src.infrastructure.config.config_manager import ConfigManager
            config = ConfigManager()
            original_headless = config.get('webdriver.headless', True)

            # Atualizar configuração temporariamente para esta thread
            config._config['webdriver']['headless'] = headless

            try:
                # 🆕 Usar CollectionExecutorService
                from .collection_executor_service import CollectionExecutorService

                executor = CollectionExecutorService()

                # Callback para atualizar progresso
                def update_progress(progress: int, action: str = ""):
                    thread_state.update_progress(progress, action)

                    # Notificar UI
                    if self.progress_callback:
                        self.progress_callback('thread_progress', thread_state.to_dict())

                # Verificar periodicamente se deve parar
                def should_stop_check() -> bool:
                    return self.state.should_stop

                # Executar busca com callbacks
                result = executor.execute_collection_for_term(
                    term=term,
                    browser=browser,
                    engine=engine,
                    headless=headless,
                    progress_callback=update_progress,
                    should_stop_callback=should_stop_check,
                    db_lock=self.db_lock
                )

                if self.state.should_stop:
                    return {'success': False, 'stopped': True}

                return {
                    'success': True,
                    'term': term,
                    'companies_found': result.get('companies_found', 0)
                }

            finally:
                # Restaurar configuração original do headless
                config._config['webdriver']['headless'] = original_headless

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

        finally:
            # Decrementar contador de threads ativas
            with self.state_lock:
                self.state.active_threads -= 1

            # Notificar UI
            if self.progress_callback:
                self.progress_callback('thread_finished', thread_state.to_dict())

    def stop_collection(self) -> Dict:
        """
        Para todas as threads em execução

        Returns:
            Dict com status da operação
        """
        if not self.state.is_running:
            return {
                'success': False,
                'message': 'Nenhuma coleta em andamento'
            }

        # Sinalizar parada
        with self.state_lock:
            self.state.should_stop = True

        # Aguardar threads finalizarem (timeout 30s)
        timeout = 30
        start_time = time.time()

        while self.state.active_threads > 0:
            if time.time() - start_time > timeout:
                break
            time.sleep(0.5)

        return {
            'success': True,
            'message': 'Coleta interrompida',
            'threads_stopped': len([t for t in self.state.threads.values() if t.status == 'stopped'])
        }

    def get_collection_status(self) -> Dict:
        """
        Retorna status atual da coleta

        Returns:
            Dict com estado completo da coleta
        """
        with self.state_lock:
            return self.state.to_dict()

    def is_running(self) -> bool:
        """Verifica se há coleta em andamento"""
        return self.state.is_running
