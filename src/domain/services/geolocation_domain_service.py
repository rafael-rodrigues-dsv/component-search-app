"""
Domain Service para operações de geolocalização
"""
from typing import Dict, List

from ...infrastructure.repositories.access_repository import AccessRepository
from ...infrastructure.services.geolocation_service import GeolocationService


class GeolocationDomainService:
    """Domain Service responsável por regras de negócio de geolocalização"""
    
    def __init__(self):
        self.repository = AccessRepository()
        self.geo_service = GeolocationService()
    
    def get_pending_geolocation_tasks(self) -> List[Dict]:
        """Obtém tarefas de geolocalização pendentes"""
        return self.repository.get_pending_geolocation_tasks()
    
    def process_single_geolocation(self, tarefa: Dict) -> Dict[str, any]:
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
            
            # Atualizar resultado na tabela de controle
            print(f"      💾 Atualizando TB_GEOLOCALIZACAO com sucesso...")
            self.repository.update_geolocation_result(id_geo, result.latitude, result.longitude, distancia_km)
            
            # Atualizar planilha final
            print(f"      💾 Atualizando TB_PLANILHA com distância...")
            self.repository.update_planilha_distance_by_empresa(empresa_id, distancia_km)
            
            return {
                'success': True,
                'latitude': result.latitude,
                'longitude': result.longitude,
                'distancia_km': distancia_km
            }
        else:
            # Tentar corrigir endereço usando geocodificação reversa ou APIs
            corrected_address = self._try_fix_address(address_model, endereco_id)
            
            if corrected_address:
                # Tentar geocodificar novamente com endereço corrigido
                result = self.geo_service.geocodificar_endereco_estruturado(corrected_address)
                
                if result.success and result.latitude and result.longitude:
                    # Calcular distância
                    distancia_km = self.geo_service.calcular_distancia(
                        self.geo_service.lat_referencia,
                        self.geo_service.lon_referencia,
                        result.latitude,
                        result.longitude
                    )
                    
                    # Atualizar TB_ENDERECOS com endereço corrigido
                    self.repository.update_endereco_corrected(endereco_id, corrected_address)
                    
                    # Atualizar resultado na tabela de controle
                    self.repository.update_geolocation_result(id_geo, result.latitude, result.longitude, distancia_km)
                    
                    # Atualizar planilha final
                    self.repository.update_planilha_distance_by_empresa(empresa_id, distancia_km)
                    
                    return {
                        'success': True,
                        'latitude': result.latitude,
                        'longitude': result.longitude,
                        'distancia_km': distancia_km,
                        'address_corrected': True
                    }
            
            # Registrar erro na tabela de controle
            endereco_str = address_model.to_full_address()
            erro_msg = f"Falha na geocodificação: {endereco_str[:100]}"
            print(f"      💾 Atualizando TB_GEOLOCALIZACAO com erro...")
            self.repository.update_geolocation_error(id_geo, erro_msg)
            
            return {
                'success': False,
                'error': erro_msg
            }
    
    def _try_fix_address(self, address_model, endereco_id) -> any:
        """Tenta corrigir endereço usando CEP ou geocodificação reversa"""
        try:
            # Se tem CEP, usar ViaCEP para corrigir
            if address_model.cep:
                from ...domain.services.address_enrichment_service import AddressEnrichmentService
                enrichment_service = AddressEnrichmentService()
                corrected = enrichment_service.enrich_address_with_cep(address_model)
                
                if enrichment_service.address_was_enriched(address_model, corrected):
                    return corrected
            
            # Se tem cidade/estado, tentar geocodificar só a cidade
            if address_model.cidade and address_model.estado:
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
        return self.repository.get_geolocation_stats()