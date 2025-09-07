"""
Domain Service para operações de banco de dados
"""
from typing import Dict, List
from ...infrastructure.repositories.access_repository import AccessRepository


class DatabaseDomainService:
    """Domain Service responsável por regras de negócio relacionadas ao banco"""
    
    def __init__(self):
        self.repository = AccessRepository()
    
    def count_total_search_terms(self) -> int:
        """Conta total de termos no banco"""
        return self.repository.count_total_search_terms()
    
    def get_pending_terms(self) -> List[Dict]:
        """Obtém termos pendentes de processamento"""
        return self.repository.get_pending_terms()
    
    def get_processing_statistics(self) -> Dict[str, int]:
        """Obtém estatísticas completas do processamento"""
        return self.repository.get_processing_statistics()
    
    def is_domain_visited(self, domain: str) -> bool:
        """Verifica se domínio já foi visitado"""
        return self.repository.is_domain_visited(domain)
    
    def is_email_collected(self, email: str) -> bool:
        """Verifica se e-mail já foi coletado"""
        return self.repository.is_email_collected(email)
    
    def save_company_data(self, termo_id: int, site_url: str, domain: str,
                          motor_busca: str, emails: list, telefones: list,
                          nome_empresa: str = None, html_content: str = None) -> bool:
        """Salva dados completos da empresa"""
        try:
            # Extrair endereço estruturado do HTML
            address_model = None

            if html_content:
                try:
                    from ...infrastructure.utils.address_extractor import AddressExtractor
                    address_model = AddressExtractor.extract_from_html(html_content)
                except Exception:
                    address_model = None

            # Salvar empresa completa
            latitude, longitude, distancia_km = None, None, None
            empresa_id = self.repository.save_empresa(termo_id, site_url, domain, motor_busca,
                                                      address_model, latitude, longitude, distancia_km)
            
            # Criar tarefas de processamento se houver endereço
            if address_model and address_model.is_valid():
                endereco_id = self.repository.save_endereco(address_model)
                if endereco_id:
                    self.repository.create_cep_enrichment_task(empresa_id, endereco_id)
                    self.repository.create_geolocation_task(empresa_id, endereco_id)

            # Sempre atualizar status da empresa (TB_EMPRESAS sempre salva)
            status = 'COLETADO' if (emails or telefones) else 'NAO_COLETADO'
            self.repository.update_empresa_status(empresa_id, status, nome_empresa)

            # Salvar nas outras tabelas APENAS se houver dados válidos
            if emails:
                domain_email = emails[0].split('@')[1] if emails else domain
                self.repository.save_emails(empresa_id, emails, domain_email)

            if telefones:
                self.repository.save_telefones(empresa_id, telefones)

            # Salvar na TB_PLANILHA apenas se houver dados coletados
            if emails or telefones:
                emails_str = ';'.join(emails) + ';' if emails else ''
                telefones_str = ';'.join([t['formatted'] for t in telefones]) + ';' if telefones else ''
                self.repository.save_to_final_sheet(site_url, emails_str, telefones_str, None)

            return True

        except Exception:
            return False
    
    def update_term_status(self, termo_id: int, status: str) -> None:
        """Atualiza status do termo processado"""
        self.repository.update_term_status(termo_id, status)
    
    def reset_collected_data(self) -> None:
        """Reset dos dados coletados"""
        self.repository.reset_collected_data()
    
    def clear_search_terms(self) -> None:
        """Limpa termos de busca existentes"""
        self.repository.clear_search_terms()
    
    def save_dynamic_search_terms(self, terms: list) -> int:
        """Salva termos de busca gerados dinamicamente"""
        return self.repository.save_dynamic_search_terms(terms)
    
    def export_to_excel(self, excel_path: str) -> int:
        """Exporta dados para Excel"""
        return self.repository.export_to_excel(excel_path)