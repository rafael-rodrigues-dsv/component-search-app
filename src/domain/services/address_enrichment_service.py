"""
Domain Service para enriquecimento de endereços via CEP
"""
from typing import Optional, List, Tuple
from ..models.address_model import AddressModel


class AddressEnrichmentService:
    """Domain Service responsável por enriquecer endereços usando CEP"""
    
    def __init__(self):
        pass
    
    def enrich_address_with_cep(self, address: AddressModel) -> AddressModel:
        """
        Enriquece endereço com dados completos do CEP se disponível
        
        Args:
            address: AddressModel com CEP
            
        Returns:
            AddressModel enriquecido ou original se falhar
        """
        if not address or not address.cep:
            return address
            
        # Buscar dados completos do CEP
        cep_data = self._fetch_cep_data(address.cep)
        if not cep_data:
            return address
            
        # Criar novo endereço enriquecido mantendo dados originais quando possível
        return AddressModel(
            logradouro=address.logradouro or cep_data.get('logradouro', ''),
            numero=address.numero,  # Manter número original
            complemento=address.complemento,  # Manter complemento original
            bairro=address.bairro or cep_data.get('bairro', ''),
            cidade=address.cidade or cep_data.get('localidade', ''),
            estado=address.estado or cep_data.get('uf', ''),
            cep=address.cep
        )
    
    def get_addresses_for_enrichment(self) -> List[Tuple[int, str, str]]:
        """
        Busca endereços com CEP que precisam de enriquecimento
        
        Returns:
            Lista de (empresa_id, endereco, cep)
        """
        from ...infrastructure.repositories.access_repository import AccessRepository
        repository = AccessRepository()
        return repository.get_addresses_with_cep_for_enrichment()
    
    def update_enriched_address(self, empresa_id: int, enriched_address: AddressModel) -> None:
        """
        Atualiza endereço enriquecido no banco de dados
        
        Args:
            empresa_id: ID da empresa
            enriched_address: AddressModel enriquecido
        """
        from ...infrastructure.repositories.access_repository import AccessRepository
        repository = AccessRepository()
        
        # Atualizar apenas TB_ENDERECOS (campos separados)
        repository.update_endereco_enriched(empresa_id, enriched_address)
        
        # TB_PLANILHA será atualizada automaticamente quando necessário
    
    def address_was_enriched(self, original: AddressModel, enriched: AddressModel) -> bool:
        """
        Verifica se o endereço foi realmente enriquecido (regra de negócio)
        
        Args:
            original: AddressModel original
            enriched: AddressModel enriquecido
            
        Returns:
            True se houve enriquecimento
        """
        # Verificar se campos foram preenchidos/melhorados
        improvements = [
            not original.logradouro and enriched.logradouro,
            not original.bairro and enriched.bairro,
            not original.cidade and enriched.cidade,
            not original.estado and enriched.estado
        ]
        
        return any(improvements)
    
    def _fetch_cep_data(self, cep: str) -> Optional[dict]:
        """
        Busca dados do CEP usando infraestrutura existente
        
        Args:
            cep: CEP limpo (8 dígitos)
            
        Returns:
            Dados do CEP ou None se falhar
        """
        try:
            # Usar infraestrutura existente do CapitalCepValidator
            from ...infrastructure.services.capital_cep_validator import CapitalCepValidator
            validator = CapitalCepValidator()
            
            # Usar método interno do validator que já tem toda a lógica
            cep_info = validator._get_cep_info(cep)
            
            if not cep_info:
                return None
                
            # Converter para formato esperado pelo ViaCEP
            return {
                'logradouro': '',  # ViaCEP pode não ter logradouro específico
                'bairro': '',      # ViaCEP pode não ter bairro específico  
                'localidade': cep_info['cidade'],
                'uf': cep_info['uf']
            }
            
        except Exception:
            return None