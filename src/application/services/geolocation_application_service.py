"""
Serviço de aplicação para processamento de geolocalização
"""
import logging
import time
from typing import Dict

from ...domain.services.geolocation_domain_service import GeolocationDomainService


class GeolocationApplicationService:
    """Serviço para processamento de geolocalização das empresas"""

    def __init__(self):
        self.domain_service = GeolocationDomainService()
        self.logger = logging.getLogger(__name__)

    def process_geolocation(self) -> Dict[str, int]:
        """Processa geolocalização usando tabela de controle"""
        try:
            # Enriquecimento CEP deve ser executado separadamente (opção [2] do menu)
            print(f"[GEO] ℹ️ Enriquecimento CEP deve ser feito antes (opção [2] do menu)")
            
            print(f"[GEO] 🔍 Verificando tarefas pendentes na TB_GEOLOCALIZACAO...")
            
            # Obter tarefas pendentes da tabela de controle
            tarefas = self.domain_service.get_pending_geolocation_tasks()
            print(f"[GEO] 📋 {len(tarefas)} tarefas encontradas na TB_GEOLOCALIZACAO")

            if not tarefas:
                print(f"[GEO] ⚠️  Nenhuma tarefa pendente - verificando se há empresas sem geolocalização...")
                # Verificar se há empresas que precisam de tarefas de geolocalização
                self._create_missing_geolocation_tasks()
                # Tentar novamente
                tarefas = self.domain_service.get_pending_geolocation_tasks()
                print(f"[GEO] 📋 Após criação: {len(tarefas)} tarefas encontradas")
                
                if not tarefas:
                    self.logger.info("✅ Nenhuma tarefa de geolocalização pendente")
                    return {'total': 0, 'processadas': 0, 'geocodificadas': 0}

            self.logger.info(f"🌍 Iniciando geolocalização de {len(tarefas)} tarefas")

            processadas = 0
            geocodificadas = 0

            for tarefa in tarefas:
                processadas += 1
                id_geo = tarefa['id_geo']
                empresa_id = tarefa['id_empresa']
                address_model = tarefa['address_model']
                site_url = tarefa['site_url']

                print(f"[GEO] 🔄 Processando {processadas}/{len(tarefas)} | Tarefa ID: {id_geo} | Empresa: {empresa_id}")
                print(f"      📍 Endereço: {address_model.to_full_address()}")
                
                # Emitir atualização WebSocket em tempo real
                self._emit_progress_update(processadas, len(tarefas), geocodificadas)

                # Processar geocodificação via Domain Service
                result = self.domain_service.process_single_geolocation(tarefa)
                
                if result['success']:
                    geocodificadas += 1
                    print(f"[GEO] ✅ Sucesso: {result['latitude']}, {result['longitude']} - {result['distancia_km']}km")
                    if result.get('address_corrected'):
                        print(f"      🔧 Endereço foi corrigido durante o processo")
                    
                    # Emitir atualização WebSocket após geocodificação
                    self._emit_progress_update(processadas, len(tarefas), geocodificadas)
                else:
                    print(f"[GEO] ❌ Falha: {result['error']}")
                
                # Pequena pausa para não sobrecarregar
                time.sleep(0.1)

            self.logger.info(f"🎯 Geolocalização concluída: {geocodificadas}/{processadas} tarefas processadas")

            return {
                'total': len(tarefas),
                'processadas': processadas,
                'geocodificadas': geocodificadas
            }

        except Exception as e:
            self.logger.error(f"Erro no processamento de geolocalização: {e}")
            return {'total': 0, 'processadas': 0, 'geocodificadas': 0}
    
    def _create_missing_geolocation_tasks(self):
        """Cria tarefas de geolocalização para empresas que não têm"""
        try:
            from ...infrastructure.repositories.access_repository import AccessRepository
            repo = AccessRepository()
            
            # Buscar empresas com endereço mas sem tarefa de geolocalização
            results = repo.fetch_all("""
                SELECT e.ID_EMPRESA, e.ID_ENDERECO 
                FROM TB_EMPRESAS e 
                WHERE e.ID_ENDERECO IS NOT NULL 
                AND NOT EXISTS (
                    SELECT 1 FROM TB_GEOLOCALIZACAO g 
                    WHERE g.ID_EMPRESA = e.ID_EMPRESA
                )
            """)
            
            print(f"[GEO] 🔧 Criando tarefas para {len(results)} empresas sem geolocalização")
            
            for empresa_id, endereco_id in results:
                repo.create_geolocation_task(empresa_id, endereco_id)
                
        except Exception as e:
            print(f"[GEO] ⚠️  Erro ao criar tarefas: {e}")



    def get_geolocation_stats(self) -> Dict[str, int]:
        """Obtém estatísticas de geolocalização da tabela de controle"""
        return self.domain_service.get_geolocation_statistics()
    
    def _emit_progress_update(self, processadas: int, total: int, geocodificadas: int):
        """Emite atualização de progresso via WebSocket"""
        try:
            # Importar aqui para evitar dependência circular
            from ...web.dashboard_server import _dashboard_server
            
            if _dashboard_server and _dashboard_server.is_running:
                # Obter estatísticas atualizadas
                stats = self.get_geolocation_stats()
                
                # Emitir via WebSocket
                _dashboard_server.socketio.emit('geo_progress', {
                    'processadas': processadas,
                    'total': total,
                    'geocodificadas': geocodificadas,
                    'percentual': stats.get('percentual', 0),
                    'pendentes': stats.get('pendentes', 0)
                })
        except Exception:
            # Falha silenciosa - não interromper processamento
            pass

    def create_task(self, empresa_id: int, endereco_id: int):
        """Compat wrapper: cria uma tarefa de geolocalização via repository"""
        try:
            from ...infrastructure.repositories.geolocation_repository import GeolocationRepository
            repo = GeolocationRepository()
            return repo.create_task(empresa_id, endereco_id)
        except Exception:
            try:
                from ...infrastructure.repositories.access_repository import AccessRepository
                repo = AccessRepository()
                return repo.create_geolocation_task(empresa_id, endereco_id)
            except Exception:
                return None

    def fetch_pending(self):
        """Retorna tarefas pendentes (compat)"""
        try:
            from ...infrastructure.repositories.geolocation_repository import GeolocationRepository
            repo = GeolocationRepository()
            return repo.fetch_pending()
        except Exception:
            try:
                from ...infrastructure.repositories.access_repository import AccessRepository
                repo = AccessRepository()
                return repo.get_pending_geolocation_tasks()
            except Exception:
                return []

    def mark_success(self, id_geo: int, lat: float, lon: float, dist_km: float):
        """Marca sucesso de geolocalização (compat)"""
        try:
            from ...infrastructure.repositories.geolocation_repository import GeolocationRepository
            repo = GeolocationRepository()
            return repo.update_success(id_geo, lat, lon, dist_km)
        except Exception:
            try:
                from ...infrastructure.repositories.access_repository import AccessRepository
                repo = AccessRepository()
                return repo.update_geolocation_success(id_geo, lat, lon, dist_km)
            except Exception:
                return False

    def mark_error(self, id_geo: int, erro: str):
        """Marca erro na tarefa de geolocalização (compat)"""
        try:
            from ...infrastructure.repositories.geolocation_repository import GeolocationRepository
            repo = GeolocationRepository()
            return repo.update_error(id_geo, erro)
        except Exception:
            try:
                from ...infrastructure.repositories.access_repository import AccessRepository
                repo = AccessRepository()
                return repo.update_geolocation_error(id_geo, erro)
            except Exception:
                return False
