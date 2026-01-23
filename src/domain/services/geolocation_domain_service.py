"""
Domain Service para operações de geolocalização
"""
from typing import Dict, List, Any

from ...infrastructure.repositories.geolocation_repository import GeolocationRepository
from ...infrastructure.repositories.addresses_repository import AddressesRepository
from ...infrastructure.services.geolocation_service import GeolocationService


class GeolocationDomainService:
    """Domain Service responsável por regras de negócio de geolocalização"""
    
    def __init__(self):
        self.geo_repo = GeolocationRepository()
        self.addresses_repo = AddressesRepository()
        self.geo_service = GeolocationService()
    
    def get_pending_geolocation_tasks(self) -> List[Dict]:
        """Obtém tarefas de geolocalização pendentes"""
        return self.geo_repo.fetch_pending()

    def process_single_geolocation(self, tarefa: Dict) -> Dict[str, Any]:
        """
        Processa uma única tarefa de geolocalização com correção de endereço
        
        Returns:
            Dict com resultado do processamento
        """
        id_geo = tarefa['id_geo']
        empresa_id = tarefa['id_empresa']
        endereco_id = tarefa['id_endereco']
        address_model = tarefa['address_model']
        
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
            
            # Atualizar resultado na tabela de controle (repo já replica para empresa e planilha)
            self.geo_repo.update_success(id_geo, result.latitude, result.longitude, distancia_km)

            return {
                'success': True,
                'latitude': result.latitude,
                'longitude': result.longitude,
                'distancia_km': distancia_km
            }
        else:
            # Tentar corrigir endereço usando geocodificação por CEP ou outras heurísticas
            corrected_address = self._try_fix_address(address_model, endereco_id)
            
            if corrected_address:
                # Atualizar endereço corrigido na TB_ENDERECOS
                try:
                    self.addresses_repo.update_corrected(endereco_id, corrected_address)
                except Exception:
                    pass

                # Tentar geocodificar novamente com endereço corrigido
                result = self.geo_service.geocodificar_endereco_estruturado(corrected_address)
                
                if result.success and result.latitude and result.longitude:
                    distancia_km = self.geo_service.calcular_distancia(
                        self.geo_service.lat_referencia,
                        self.geo_service.lon_referencia,
                        result.latitude,
                        result.longitude
                    )

                    # Atualizar resultado na tabela de controle
                    self.geo_repo.update_success(id_geo, result.latitude, result.longitude, distancia_km)

                    return {
                        'success': True,
                        'latitude': result.latitude,
                        'longitude': result.longitude,
                        'distancia_km': distancia_km,
                        'address_corrected': True
                    }
            
            # Registrar erro na tabela de controle
            endereco_str = address_model.to_full_address() if hasattr(address_model, 'to_full_address') else str(address_model)
            erro_msg = f"Falha na geocodificação: {endereco_str[:100]}"
            self.geo_repo.update_error(id_geo, erro_msg)

            return {
                'success': False,
                'error': erro_msg
            }
    
    def _try_fix_address(self, address_model, endereco_id) -> Any:
        """Tenta corrigir endereço usando CEP ou geocodificação reversa"""
        try:
            # Se tem CEP, usar AddressEnrichmentService (domain)
            if getattr(address_model, 'cep', None):
                try:
                    from ...domain.services.address_enrichment_service import AddressEnrichmentService
                    enrichment_service = AddressEnrichmentService()
                    corrected = enrichment_service.enrich_address_with_cep(address_model)
                    if corrected and enrichment_service.address_was_enriched(address_model, corrected):
                        return corrected
                except Exception:
                    pass

            # Se tem cidade/estado, tentar geocodificar apenas a cidade como fallback
            if getattr(address_model, 'cidade', None) and getattr(address_model, 'estado', None):
                from ...domain.models.address_model import AddressModel
                city_address = AddressModel(
                    logradouro="",
                    numero="",
                    complemento="",
                    bairro=address_model.bairro or "",
                    cidade=address_model.cidade,
                    estado=address_model.estado,
                    cep=""
                )
                return city_address

            return None
        except Exception:
            return None
    
    def get_geolocation_statistics(self) -> Dict[str, int]:
        """Obtém estatísticas de geolocalização"""
        return self.geo_repo.get_stats()
