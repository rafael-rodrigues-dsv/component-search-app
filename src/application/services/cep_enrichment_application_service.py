"""
Application Service para enriquecimento de endereços via CEP (separado)
"""
import time
from typing import Dict
import threading

from ...domain.services.address_enrichment_service import AddressEnrichmentService
from ...infrastructure.repositories.cep_enrichment_repository import CepEnrichmentRepository


class CepEnrichmentApplicationService:
    """Application Service que coordena apenas o enriquecimento via CEP"""
    
    def __init__(self):
        self.domain_service = AddressEnrichmentService()
        self.repository = CepEnrichmentRepository()

    def _enrich_with_timeout(self, address_model, timeout=12.0):
        """Call domain_service.enrich_address_with_cep in a thread with timeout.
        Returns (enriched_address, error_str) where error_str is None on success.
        """
        from typing import Dict, Any
        container: Dict[str, Any] = {'result': None, 'error': None}
        def worker():
            try:
                res = self.domain_service.enrich_address_with_cep(address_model)
                container['result'] = res
            except Exception as e:
                container['error'] = str(e)
        th = threading.Thread(target=worker, daemon=True)
        th.start()
        th.join(timeout)
        if th.is_alive():
            return None, f"timeout after {timeout}s"
        return container.get('result'), container.get('error')

    def process_cep_enrichment(self) -> Dict[str, int]:
        """
        Processa apenas enriquecimento via CEP (sem geolocalização)
        
        Returns:
            Dict com estatísticas do processamento
        """
        print("[CEP] 🔍 Iniciando enriquecimento via ViaCEP...")
        # Emitir log ao dashboard (garante visibilidade na UI)
        self._emit_log('info', '[CEP] 🔍 Iniciando enriquecimento via ViaCEP...')

        # Obter tarefas pendentes (medir tempo para diagnosticar bloqueios)
        t0 = time.time()
        tasks = self.repository.fetch_pending()
        fetch_dt = time.time() - t0
        msg = f"[CEP] ⏱️ fetch_pending levou {fetch_dt:.2f}s e retornou {len(tasks) if tasks is not None else 0} itens"
        print(msg)
        self._emit_log('info', msg)

        if not tasks:
            print("[CEP] ℹ️  Nenhuma tarefa de enriquecimento CEP pendente")
            return {'total': 0, 'processadas': 0, 'enriquecidas': 0}
        
        print(f"[CEP] 📋 {len(tasks)} tarefas encontradas")
        
        processadas = 0
        enriquecidas = 0
        
        for task in tasks:
            processadas += 1
            id_cep_enrichment = task['id_cep_enrichment']
            empresa_id = task['id_empresa']
            endereco_id = task['id_endereco']
            address_model = task['address_model']
            site_url = task['site_url']
            
            msg = f"[CEP] 🔄 Processando {processadas}/{len(tasks)} | Empresa: {empresa_id}"
            print(msg)
            self._emit_log('info', msg)
            print(f"      📍 Endereço: {address_model.to_full_address()}")
            print(f"      🏠 CEP: {address_model.cep}")
            
            # Emitir atualização WebSocket em tempo real
            self._emit_progress_update(processadas, len(tasks), enriquecidas)
            
            try:
                # Validar CEP antes de processar
                if not address_model.cep or address_model.cep.strip() == '':
                    print(f"      ⚠️ CEP vazio ou nulo")
                    self.repository.update_error(id_cep_enrichment, "CEP vazio ou nulo")
                    continue
                
                # Enriquecer com dados do CEP
                if len(address_model.cep.strip()) >= 8:
                    msg = f"      🔍 Consultando ViaCEP..."
                    print(msg)
                    self._emit_log('info', msg)
                    enriched_address, enrich_err = self._enrich_with_timeout(address_model, timeout=12.0)
                    if enrich_err:
                        err_msg = f"      ❌ Enriquecimento falhou: {enrich_err}"
                        print(err_msg)
                        self._emit_log('error', err_msg)
                        self.repository.update_error(id_cep_enrichment, f"ViaCEP error: {enrich_err}")
                        continue
                    if enriched_address is None:
                        print(f"      ❌ Enriquecimento retornou None")
                        self.repository.update_error(id_cep_enrichment, "ViaCEP returned no data")
                        continue

                    # Debug: comparar endereços
                    print(f"      🔍 ANTES: {address_model.to_full_address()}")
                    print(f"      🔍 DEPOIS: {enriched_address.to_full_address()}")
                    
                    # Verificar se houve enriquecimento
                    if self.domain_service.address_was_enriched(address_model, enriched_address):
                        print(f"      ✨ Enriquecido: {enriched_address.to_full_address()}")
                        print(f"      💾 Atualizando TB_ENDERECOS...")
                        
                        # Atualizar endereço na TB_ENDERECOS através do AddressesRepository
                        try:
                            from src.infrastructure.repositories.addresses_repository import AddressesRepository
                            addr_repo = AddressesRepository()
                            addr_repo.update_corrected(endereco_id, enriched_address)
                        except Exception as e:
                            err_msg = f"      ⚠️ Falha ao atualizar TB_ENDERECOS: {e}"
                            print(err_msg)
                            self._emit_log('error', err_msg)
                            # continue processing but mark error later if needed

                        # Marcar como concluído
                        try:
                            self.repository.update_success(id_cep_enrichment)
                        except Exception as e:
                            err_msg = f"      ⚠️ Falha ao marcar sucesso na TB_CEP_ENRICHMENT: {e}"
                            print(err_msg)
                            self._emit_log('error', err_msg)
                        enriquecidas += 1

                        ok_msg = f"      ✅ Empresa {empresa_id} enriquecida com sucesso"
                        print(ok_msg)
                        self._emit_log('info', ok_msg)

                        # Emitir atualização WebSocket após enriquecimento
                        self._emit_progress_update(processadas, len(tasks), enriquecidas)
                    else:
                        warn_msg = f"      ⚠️ CEP não melhorou o endereço (sem diferenças significativas)"
                        print(warn_msg)
                        self._emit_log('warning', warn_msg)
                        self.repository.update_error(id_cep_enrichment, "CEP não melhorou o endereço")
                else:
                    invalid_msg = f"      ⚠️ CEP inválido"
                    print(invalid_msg)
                    self._emit_log('warning', invalid_msg)
                    self.repository.update_error(id_cep_enrichment, "CEP inválido ou ausente")

            except Exception as e:
                err_msg = f"      ❌ Erro: {e}"
                print(err_msg)
                self._emit_log('error', err_msg)
                self.repository.update_error(id_cep_enrichment, str(e)[:255])

            # Pequena pausa para não sobrecarregar
            time.sleep(0.1)
        
        done_msg = f"[CEP] 🎯 Processamento concluído: {processadas} processadas, {enriquecidas} enriquecidas"
        print(done_msg)
        self._emit_log('info', done_msg)
        print(f"[CEP] ✅ TB_ENDERECOS atualizada com dados do ViaCEP")
        self._emit_log('info', '[CEP] ✅ TB_ENDERECOS atualizada com dados do ViaCEP')

        return {
            'total': len(tasks),
            'processadas': processadas,
            'enriquecidas': enriquecidas
        }
    
    def create_cep_enrichment_tasks(self) -> int:
        """Cria tarefas de enriquecimento CEP para empresas com CEP"""
        print("[CEP] 🔧 Criando tarefas de enriquecimento CEP...")
        
        # Buscar empresas com CEP que não têm tarefa de enriquecimento
        results = self.repository.fetch_all("""
            SELECT e.ID_EMPRESA, e.ID_ENDERECO 
            FROM TB_EMPRESAS e 
            INNER JOIN TB_ENDERECOS en ON e.ID_ENDERECO = en.ID_ENDERECO
            WHERE en.CEP IS NOT NULL 
            AND en.CEP <> ''
            AND NOT EXISTS (
                SELECT 1 FROM TB_CEP_ENRICHMENT c 
                WHERE c.ID_EMPRESA = e.ID_EMPRESA
            )
        """)
        
        print(f"[CEP] 📋 Criando {len(results)} tarefas...")
        
        for empresa_id, endereco_id in results:
            self.repository.create_task(empresa_id, endereco_id)

        print(f"[CEP] ✅ {len(results)} tarefas criadas na TB_CEP_ENRICHMENT")
        return len(results)
    
    def get_cep_enrichment_stats(self) -> Dict[str, int]:
        """Obtém estatísticas de enriquecimento CEP"""
        return self.repository.stats()

    def get_paginated_tasks(self, limit: int = 10, offset: int = 0):
        try:
            total = self.repository.count()
            models = self.repository.fetch_models_paginated(limit=limit, offset=offset)
            items = [m.to_api_dict() for m in models]
            try:
                limit = int(limit) if limit else 10
                offset = int(offset) if offset else 0
            except Exception:
                limit = 10
                offset = 0
            total_pages = (total + limit - 1) // limit if limit > 0 else 1
            current_page = (offset // limit) + 1 if limit > 0 else 1
            return {'tasks': items, 'pagination': {'total': total, 'limit': limit, 'offset': offset, 'total_pages': total_pages, 'current_page': current_page, 'has_next': current_page < total_pages, 'has_previous': current_page > 1}}
        except Exception:
            return {'tasks': [], 'pagination': {'total': 0, 'limit': limit, 'offset': offset, 'total_pages': 1, 'current_page': 1, 'has_next': False, 'has_previous': False}}

    def _emit_progress_update(self, processadas: int, total: int, enriquecidas: int):
         """Emite atualização de progresso via WebSocket (simples).
         Emite apenas os campos necessários para o front: 'enriquecidas', 'pendentes', 'percentual'.
         Não faz chamadas adicionais ao banco nem emite logs extras.
         """
         try:
             from ...web.dashboard_server import _dashboard_server
             if not _dashboard_server:
                 return
             socketio = getattr(_dashboard_server, 'socketio', None)
             if not socketio:
                 return

             pendentes = max(total - processadas, 0)
             percentual = round((enriquecidas / max(total, 1)) * 100, 1)

             payload = {
                 'enriquecidas': enriquecidas,
                 'pendentes': pendentes,
                 'percentual': percentual
             }

             try:
                 socketio.emit('cep_progress', payload)
             except Exception:
                 # não propagar erro de socket
                 pass
         except Exception:
             pass

    def _emit_log(self, level: str, message: str):
        """Emite mensagens de log para o dashboard via SocketIO (robot_log)."""
        try:
            from ...web.dashboard_server import _dashboard_server
            if not _dashboard_server:
                return
            socketio = getattr(_dashboard_server, 'socketio', None)
            if not socketio:
                return
            try:
                socketio.emit('robot_log', {'level': level, 'message': message})
            except Exception:
                pass
        except Exception:
             # Fallback silencioso
             pass

    def create_task(self, empresa_id: int, endereco_id: int):
        """Compat layer: cria uma única tarefa (thin wrapper)"""
        return self.repository.create_task(empresa_id, endereco_id)

    def fetch_pending(self):
        """Retorna tarefas pendentes (wrapper para uso simples em outros módulos)"""
        return self.repository.fetch_pending()

    def mark_success(self, id_cep_enrichment: int):
        """Marca tarefa como concluída"""
        return self.repository.update_success(id_cep_enrichment)

    def mark_error(self, id_cep_enrichment: int, err: str):
        """Marca tarefa com erro"""
        return self.repository.update_error(id_cep_enrichment, err)

    def stats(self):
        """Retorna estatísticas (compat)"""
        return self.get_cep_enrichment_stats()
