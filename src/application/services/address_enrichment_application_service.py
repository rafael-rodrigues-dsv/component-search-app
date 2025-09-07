"""
Application Service para enriquecimento de endereços durante geolocalização
"""
from typing import List, Tuple
from ...domain.services.address_enrichment_service import AddressEnrichmentService


class AddressEnrichmentApplicationService:
    """Application Service que coordena o enriquecimento de endereços"""
    
    def __init__(self):
        self.domain_service = AddressEnrichmentService()
    
    def enrich_addresses_for_geolocation(self) -> Tuple[int, int]:
        """
        Método legado - tarefas são criadas durante o scraping
        
        Returns:
            Tuple (0, 0)
        """
        print("[GEO] 🔍 Verificando endereços com CEP para enriquecimento...")
        
        # Buscar endereços com CEP que ainda não foram geocodificados
        addresses_to_enrich = self.domain_service.get_addresses_for_enrichment()
        
        if not addresses_to_enrich:
            print("[GEO] ℹ️  Nenhum endereço com CEP encontrado para enriquecimento")
            return 0, 0
            
        print(f"[GEO] 📋 {len(addresses_to_enrich)} endereços com CEP encontrados")
        
        enriched_count = 0
        
        for empresa_id, endereco_original, cep in addresses_to_enrich:
            try:
                print(f"[GEO] 🔍 Processando empresa {empresa_id}:")
                print(f"      📍 Original: {endereco_original}")
                print(f"      🏠 CEP: {cep}")
                
                # Criar AddressModel do endereço atual
                from ...infrastructure.utils.address_extractor import AddressExtractor
                from ...domain.models.address_model import AddressModel
                
                # Parse do endereço original
                address_parts = endereco_original.split(', ')
                print(f"      🔧 Partes: {address_parts}")
                
                # Separar número e complemento se existir
                numero_completo = address_parts[1] if len(address_parts) > 1 else ''
                numero, complemento = self._parse_numero_complemento(numero_completo)
                print(f"      🔢 Número: '{numero}' | Complemento: '{complemento}'")
                
                current_address = AddressModel(
                    logradouro=address_parts[0] if len(address_parts) > 0 else '',
                    numero=numero,
                    complemento=complemento,
                    bairro=address_parts[2] if len(address_parts) > 2 else '',
                    cidade=address_parts[3] if len(address_parts) > 3 else '',
                    estado=address_parts[4] if len(address_parts) > 4 else '',
                    cep=cep
                )
                
                print(f"      🏠 Estruturado: {current_address.to_full_address()}")
                
                # Enriquecer com dados do CEP (só se tiver CEP)
                if cep and len(cep.strip()) >= 8:
                    print(f"      🔍 Consultando CEP {cep}...")
                    enriched_address = self.domain_service.enrich_address_with_cep(current_address)
                else:
                    print(f"      ⚠️ CEP inválido ou ausente - pulando enriquecimento")
                    enriched_address = current_address
                
                # Criar tarefa de enriquecimento CEP
                from ...infrastructure.repositories.access_repository import AccessRepository
                repo = AccessRepository()
                result = repo.fetch_one("SELECT ID_ENDERECO FROM TB_EMPRESAS WHERE ID_EMPRESA = ?", [empresa_id])
                
                if result:
                    endereco_id = result[0]
                    
                    # Criar tarefa na TB_CEP_ENRICHMENT
                    repo.create_cep_enrichment_task(empresa_id, endereco_id)
                    print(f"      📋 Tarefa criada na TB_CEP_ENRICHMENT")
                    
                    # Contar como processado para estatísticas
                    enriched_count += 1
                
            except Exception as e:
                print(f"[GEO] ⚠️  Erro ao processar empresa {empresa_id}: {e}")
                continue
        
        print(f"[GEO] ℹ️ Tarefas de enriquecimento são criadas automaticamente durante o scraping")
        print(f"[GEO] ℹ️ Use a opção [2] do menu para processar enriquecimento ViaCEP")
        print(f"[GEO] ℹ️ Use a opção [3] do menu para processar geolocalização Nominatim")
        return len(addresses_to_enrich), enriched_count
    

    
    def _parse_numero_complemento(self, numero_completo: str) -> tuple[str, str]:
        """Separa número e complemento de string existente"""
        if not numero_completo:
            return "", ""
            
        import re
        
        # Padrões para separar número de complemento
        patterns = [
            r'^(\d+)\s+(.+)$',  # "123 Apto 45"
            r'^(\d+)([A-Za-z].*)$',  # "123A" ou "123-A"
            r'^(\d+)$'  # Apenas número
        ]
        
        for pattern in patterns:
            match = re.match(pattern, numero_completo.strip())
            if match:
                if len(match.groups()) == 2:
                    numero, complemento = match.groups()
                    return numero.strip(), complemento.strip()
                else:
                    return match.group(1).strip(), ""
        
        # Fallback: tudo como número
        return numero_completo.strip(), ""