"""
Application Service para enriquecimento de endereços via CEP (separado)
"""
from typing import Dict
from ...domain.services.address_enrichment_service import AddressEnrichmentService
from ...infrastructure.repositories.access_repository import AccessRepository


class CepEnrichmentApplicationService:
    """Application Service que coordena apenas o enriquecimento via CEP"""
    
    def __init__(self):
        self.domain_service = AddressEnrichmentService()
        self.repository = AccessRepository()
    
    def process_cep_enrichment(self) -> Dict[str, int]:
        """
        Processa apenas enriquecimento via CEP (sem geolocalização)
        
        Returns:
            Dict com estatísticas do processamento
        """
        print("[CEP] 🔍 Iniciando enriquecimento via ViaCEP...")
        
        # Obter tarefas pendentes
        tasks = self.repository.get_pending_cep_enrichment_tasks()
        
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
            
            print(f"[CEP] 🔄 Processando {processadas}/{len(tasks)} | Empresa: {empresa_id}")
            print(f"      📍 Endereço: {address_model.to_full_address()}")
            print(f"      🏠 CEP: {address_model.cep}")
            
            try:
                # Enriquecer com dados do CEP
                if address_model.cep and len(address_model.cep.strip()) >= 8:
                    print(f"      🔍 Consultando ViaCEP...")
                    enriched_address = self.domain_service.enrich_address_with_cep(address_model)
                    
                    # Verificar se houve enriquecimento
                    if self.domain_service.address_was_enriched(address_model, enriched_address):
                        print(f"      ✨ Enriquecido: {enriched_address.to_full_address()}")
                        print(f"      💾 Atualizando TB_ENDERECOS...")
                        
                        # Atualizar endereço na TB_ENDERECOS
                        self.repository.update_endereco_corrected(endereco_id, enriched_address)
                        
                        # Marcar como concluído
                        self.repository.update_cep_enrichment_success(id_cep_enrichment)
                        enriquecidas += 1
                        
                        print(f"      ✅ Empresa {empresa_id} enriquecida com sucesso")
                    else:
                        print(f"      ⚠️ CEP não melhorou o endereço")
                        self.repository.update_cep_enrichment_error(id_cep_enrichment, "CEP não melhorou o endereço")
                else:
                    print(f"      ⚠️ CEP inválido")
                    self.repository.update_cep_enrichment_error(id_cep_enrichment, "CEP inválido ou ausente")
                    
            except Exception as e:
                print(f"      ❌ Erro: {e}")
                self.repository.update_cep_enrichment_error(id_cep_enrichment, str(e)[:255])
        
        print(f"[CEP] 🎯 Processamento concluído:")
        print(f"      📋 {processadas} tarefas processadas")
        print(f"      ✨ {enriquecidas} endereços enriquecidos")
        print(f"[CEP] ✅ TB_ENDERECOS atualizada com dados do ViaCEP")
        
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
            self.repository.create_cep_enrichment_task(empresa_id, endereco_id)
        
        print(f"[CEP] ✅ {len(results)} tarefas criadas na TB_CEP_ENRICHMENT")
        return len(results)
    
    def get_cep_enrichment_stats(self) -> Dict[str, int]:
        """Obtém estatísticas de enriquecimento CEP"""
        return self.repository.get_cep_enrichment_stats()