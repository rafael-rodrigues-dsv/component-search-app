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
            
        # Criar novo endereço enriquecido combinando dados de forma inteligente
        return AddressModel(
            logradouro=self._choose_best_value(address.logradouro, cep_data.get('logradouro', '')),
            numero=address.numero,  # Manter número original
            complemento=address.complemento,  # Manter complemento original
            bairro=self._choose_best_value(address.bairro, cep_data.get('bairro', '')),
            cidade=self._choose_best_value(address.cidade, cep_data.get('localidade', '')),
            estado=self._choose_best_value(address.estado, cep_data.get('uf', '')),
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
        Verifica se API realmente melhorou os dados
        """
        # Verificar se houve melhoria real nos dados
        improvements = []
        
        # Campo foi preenchido
        if (not original.logradouro or original.logradouro.strip() == '') and enriched.logradouro and enriched.logradouro.strip():
            improvements.append('logradouro')
        if (not original.bairro or original.bairro.strip() == '') and enriched.bairro and enriched.bairro.strip():
            improvements.append('bairro')
        if (not original.cidade or original.cidade.strip() == '') and enriched.cidade and enriched.cidade.strip():
            improvements.append('cidade')
        if (not original.estado or original.estado.strip() == '') and enriched.estado and enriched.estado.strip():
            improvements.append('estado')
            
        # Campo foi corrigido
        if original.cidade and enriched.cidade and enriched.cidade.strip() != original.cidade.strip():
            improvements.append('cidade_corrigida')
        if original.estado and enriched.estado and enriched.estado.strip() != original.estado.strip():
            improvements.append('estado_corrigido')
        
        if improvements:
            print(f"      ✨ Melhorias: {', '.join(improvements)}")
            return True
        else:
            print(f"      ⚠️ Sem melhorias detectadas")
            return False
    
    def _choose_best_value(self, original: str, api_data: str) -> str:
        """
        ESTRATÉGIA AGRESSIVA: Sempre priorizar dados da API quando disponível
        """
        # Se API tem dados, SEMPRE usar (dados oficiais)
        if api_data and api_data.strip():
            return api_data.strip()

        # Caso contrário, manter original
        return original or ''
    
    def _fetch_cep_data(self, cep: str) -> Optional[dict]:
        """
        Busca dados do CEP usando BrasilAPI com cache

        Args:
            cep: CEP (8 dígitos ou com hífen)
            
        Returns:
            Dados do CEP ou None se falhar
        """
        try:
            import requests
            import re
            
            # Limpar CEP (remover caracteres não numéricos)
            cep_clean = re.sub(r'\D', '', cep)
            
            # Tentar corrigir CEPs mal formatados
            if len(cep_clean) < 8:
                cep_clean = cep_clean.zfill(8)
            elif len(cep_clean) > 8:
                cep_clean = cep_clean[:8]
            
            # Validar CEP final
            if len(cep_clean) != 8 or not cep_clean.isdigit():
                print(f"      ❌ CEP inválido: {cep} (limpo: {cep_clean})")
                return None
                
            print(f"      🔧 CEP processado: {cep} -> {cep_clean}")
            
            # Usar CepResolverService (BrasilAPI + Cache)
            from ...infrastructure.services.cep_resolver_service import CepResolverService
            cep_service = CepResolverService()

            # Tentar CEP original
            data = cep_service.get_cep_data(cep_clean)
            if data:
                return data
                
            # Fallback: CEPs similares
            print(f"      🔄 Tentando CEPs similares...")
            similar_ceps = self._generate_similar_ceps(cep_clean)
            
            for similar_cep in similar_ceps[:2]:
                print(f"      🔍 CEP similar: {similar_cep}")

                data = cep_service.get_cep_data(similar_cep)
                if data:
                    print(f"      ✅ CEP similar funcionou: {data}")
                    return data
                else:
                    print(f"      ❌ CEP similar falhou")
            
            return None
            
        except Exception:
            return None
    
    def _generate_similar_ceps(self, cep_clean: str) -> List[str]:
        """Gera CEPs similares para fallback"""
        similar_ceps = []
        
        # Tentar com último dígito 0 (CEPs genéricos)
        if cep_clean[-1] != '0':
            similar_ceps.append(cep_clean[:-1] + '0')
            
        # Tentar com últimos 2 dígitos 00
        if not cep_clean.endswith('00'):
            similar_ceps.append(cep_clean[:-2] + '00')
            
        # Tentar com últimos 3 dígitos 000
        if not cep_clean.endswith('000'):
            similar_ceps.append(cep_clean[:-3] + '000')
            
        return similar_ceps