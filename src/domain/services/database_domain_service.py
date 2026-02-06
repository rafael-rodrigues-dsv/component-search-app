"""
Domain Service para operações de banco de dados (refatorado para usar repositories específicos)
"""
from typing import Dict, List

from ...infrastructure.repositories.terms_repository import TermsRepository
from ...infrastructure.repositories.companies_repository import CompaniesRepository
from ...infrastructure.repositories.addresses_repository import AddressesRepository
from ...infrastructure.repositories.emails_repository import EmailsRepository
from ...infrastructure.repositories.phones_repository import PhonesRepository
from ...infrastructure.repositories.spreadsheet_repository import SpreadsheetRepository
from ...infrastructure.repositories.geolocation_repository import GeolocationRepository
from ...infrastructure.repositories.cep_enrichment_repository import CepEnrichmentRepository
from ...infrastructure.repositories.statistics_repository import StatisticsRepository


class DatabaseDomainService:
    """Domain Service responsável por regras de negócio relacionadas ao banco"""

    def __init__(self):
        # Instantiate specific repositories
        self.terms_repo = TermsRepository()
        self.companies_repo = CompaniesRepository()
        self.addresses_repo = AddressesRepository()
        self.emails_repo = EmailsRepository()
        self.phones_repo = PhonesRepository()
        self.spreadsheet_repo = SpreadsheetRepository()
        self.geo_repo = GeolocationRepository()
        self.cep_repo = CepEnrichmentRepository()
        self._stats = StatisticsRepository()  # aggregated stats

    def count_total_search_terms(self) -> int:
        return self.terms_repo.count()

    def get_pending_terms(self) -> List[Dict]:
        return self.terms_repo.fetch_pending()

    def get_processing_statistics(self) -> Dict[str, int]:
        try:
            return self._stats.get_processing_statistics()
        except Exception:
            return {
                'termos_total': 0,
                'termos_concluidos': 0,
                'termos_pendentes': 0,
                'empresas_total': 0,
                'empresas_coletadas': 0,
                'emails_total': 0,
                'telefones_total': 0,
                'progresso_pct': 0
            }

    def get_company_collection_statistics(self) -> Dict[str, int]:
        try:
            return self.companies_repo.get_collection_statistics()
        except Exception:
            return {'visitadas': 0, 'coletadas': 0, 'nao_coletadas': 0, 'taxa_coleta_pct': 0}

    def is_domain_visited(self, domain: str) -> bool:
        return self.companies_repo.is_domain_visited(domain)

    def is_email_collected(self, email: str) -> bool:
        return self.emails_repo.is_email_collected(email)

    def save_company_data(self, termo_id: int, site_url: str, domain: str,
                          motor_busca: str, emails: list, telefones: list,
                          nome_empresa: str = None, html_content: str = None) -> bool:
        """Salva dados completos da empresa usando os repositories apropriados"""
        try:
            # Extrair endereço estruturado do HTML (se houver)
            address_model = None
            if html_content:
                try:
                    from ...infrastructure.utils.address_extractor import AddressExtractor
                    address_model = AddressExtractor.extract_from_html(html_content)
                except Exception:
                    address_model = None

            # Inserir empresa (companies repository handles address insertion if provided)
            empresa_id = self.companies_repo.insert_company(termo_id, site_url, domain, motor_busca, address_model)

            # Se address_model válido, garantir endereço e criar tarefas
            if address_model and hasattr(address_model, 'is_valid') and address_model.is_valid():
                endereco_id = self.addresses_repo.insert_address(address_model)
                if endereco_id:
                    self.cep_repo.create_task(empresa_id, endereco_id)
                    self.geo_repo.create_task(empresa_id, endereco_id)

            # Extrair endereço formatado se existir
            endereco_str = ''
            if address_model and hasattr(address_model, 'to_full_address'):
                try:
                    endereco_str = address_model.to_full_address()
                except:
                    pass

            # ✅ Atualizar status considerando endereço também
            status = 'COLETADO' if (emails or telefones or endereco_str) else 'NAO_COLETADO'
            self.companies_repo.update_status(empresa_id, status, nome_empresa)

            # Salvar emails
            if emails:
                domain_email = emails[0].split('@')[1] if emails else domain
                self.emails_repo.insert_emails(empresa_id, emails, domain_email)

            # Salvar telefones (converter para formato esperado)
            if telefones:
                # Verificar se já vem como lista de dicts ou lista de strings
                if telefones and isinstance(telefones[0], str):
                    # Converter strings para formato dict esperado
                    telefones_formatted = []
                    for tel in telefones:
                        telefones_formatted.append({
                            'original': tel,
                            'formatted': tel,
                            'ddd': '',
                            'tipo': 'FIXO'
                        })
                    self.phones_repo.insert_phones(empresa_id, telefones_formatted)
                else:
                    # Já vem como dicts
                    self.phones_repo.insert_phones(empresa_id, telefones)

            # ✅ SALVAR NA PLANILHA APENAS SE TIVER DADOS COLETADOS
            # (email, telefone OU endereço)
            if emails or telefones or endereco_str:
                emails_str = ';'.join(emails) + ';' if emails else ''

                # Montar string de telefones
                if telefones:
                    if isinstance(telefones[0], dict):
                        telefones_str = ';'.join([t['formatted'] for t in telefones]) + ';'
                    else:
                        telefones_str = ';'.join(telefones) + ';'
                else:
                    telefones_str = ''

                self.spreadsheet_repo.save_to_sheet(site_url, emails_str, telefones_str, endereco_str, None)

            return True
        except Exception:
            return False

    def update_term_status(self, termo_id: int, status: str) -> None:
        self.terms_repo.update_status(termo_id, status)

    def reset_collected_data(self) -> None:
        # Use MaintenanceRepository for multi-table deletes and reset logic
        try:
            from ...infrastructure.repositories.maintenance_repository import MaintenanceRepository
            repo = MaintenanceRepository()
            repo.reset_collected_data()
        except Exception:
            pass

    def clear_search_terms(self) -> None:
        self.terms_repo.delete_all()

    def save_dynamic_search_terms(self, terms: list) -> int:
        # Prefer using TermsRepository bulk insert
        try:
            return self.terms_repo.bulk_insert(terms)
        except Exception:
            # Fallback: insert one-by-one via TermsRepository.insert
            inserted = 0
            try:
                for t in terms:
                    if isinstance(t, dict):
                        termo = t.get('termo') or t.get('termo_completo') or t.get('termo')
                        tipo = t.get('tipo_localizacao') or t.get('tipo') or ''
                    else:
                        termo = str(t)
                        tipo = ''
                    if termo:
                        self.terms_repo.insert(termo, tipo)
                        inserted += 1
                return inserted
            except Exception:
                return 0

    def export_to_excel(self, excel_path: str) -> int:
        return self.spreadsheet_repo.export_to_excel(excel_path)
