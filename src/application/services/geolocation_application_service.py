"""
Serviço de aplicação para processamento de geolocalização
"""
import logging
from typing import List, Dict

from src.infrastructure.repositories.access_repository import AccessRepository
from src.infrastructure.services.geolocation_service import GeolocationService


class GeolocationApplicationService:
    """Serviço para processamento de geolocalização das empresas"""

    def __init__(self):
        self.repository = AccessRepository()
        self.geo_service = GeolocationService()
        self.logger = logging.getLogger(__name__)

    def process_geolocation(self) -> Dict[str, int]:
        """Processa geolocalização usando tabela de controle"""
        try:
            # Obter tarefas pendentes da tabela de controle
            tarefas = self.repository.get_pending_geolocation_tasks()

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

                self.logger.info(f"[GEO] Processando {processadas}/{len(tarefas)} | Tarefa: {id_geo}")

                # Geocodificar endereço estruturado
                result = self.geo_service.geocodificar_endereco_estruturado(address_model)

                if result.success and result.latitude and result.longitude:
                    # Calcular distância
                    distancia_km = self.geo_service.calcular_distancia(
                        self.geo_service.lat_referencia,
                        self.geo_service.lon_referencia,
                        result.latitude,
                        result.longitude
                    )

                    # Atualizar resultado na tabela de controle (replica automaticamente)
                    self.repository.update_geolocation_result(id_geo, result.latitude, result.longitude, distancia_km)

                    # Atualizar planilha final
                    self.repository.update_planilha_distance_by_empresa(empresa_id, distancia_km)

                    geocodificadas += 1
                    self.logger.info(f"[GEO] ✅ Geocodificada: {result.latitude}, {result.longitude} - {distancia_km}km")
                else:
                    # Registrar erro na tabela de controle
                    endereco_str = address_model.to_full_address()
                    erro_msg = f"Falha na geocodificação: {endereco_str[:100]}"
                    self.repository.update_geolocation_error(id_geo, erro_msg)
                    self.logger.debug(f"[GEO] ❌ {erro_msg}")

            self.logger.info(f"🎯 Geolocalização concluída: {geocodificadas}/{processadas} tarefas processadas")

            return {
                'total': len(tarefas),
                'processadas': processadas,
                'geocodificadas': geocodificadas
            }

        except Exception as e:
            self.logger.error(f"Erro no processamento de geolocalização: {e}")
            return {'total': 0, 'processadas': 0, 'geocodificadas': 0}



    def get_geolocation_stats(self) -> Dict[str, int]:
        """Obtém estatísticas de geolocalização da tabela de controle"""
        return self.repository.get_geolocation_stats()
