"""
Serviço de aplicação para gerenciamento do banco de dados
"""
import logging
from pathlib import Path

from src.infrastructure.repositories.access_repository import AccessRepository


class DatabaseService:
    """Serviço para operações de banco de dados"""

    def __init__(self):
        self.repository = AccessRepository()
        self.logger = logging.getLogger(__name__)

    def initialize_search_terms(self) -> int:
        """Inicializa termos de busca se necessário"""
        try:
            pending_terms = self.repository.get_pending_terms()

            if not pending_terms:
                self.logger.info("Gerando termos de busca...")
                count = self.repository.generate_search_terms()
                self.logger.info(f"✅ {count} termos de busca gerados")
                return count
            else:
                self.logger.info(f"✅ {len(pending_terms)} termos já existem")
                return len(pending_terms)

        except Exception as e:
            self.logger.error(f"Erro ao inicializar termos: {e}")
            return 0

    def get_search_terms(self) -> list:
        """Obtém lista de termos para processamento"""
        return self.repository.get_pending_terms()

    def is_domain_visited(self, domain: str) -> bool:
        """Verifica se domínio já foi visitado"""
        return self.repository.is_domain_visited(domain)

    def is_email_collected(self, email: str) -> bool:
        """Verifica se e-mail já foi coletado"""
        return self.repository.is_email_collected(email)

    def save_company_data(self, termo_id: int, site_url: str, domain: str,
                          motor_busca: str, emails: list, telefones: list,
                          nome_empresa: str = None, html_content: str = None,
                          termo_busca: str = None) -> bool:
        """Salva dados completos da empresa"""
        try:
            # Extrair endereço estruturado do HTML
            address_model = None

            if html_content:
                try:
                    from src.infrastructure.utils.address_extractor import AddressExtractor
                    address_model = AddressExtractor.extract_from_html(html_content)

                    if address_model and address_model.is_valid():
                        self.logger.debug(f"[ADDR] Endereco extraido: {address_model.to_full_address()[:50]}...")
                    else:
                        self.logger.debug("[ADDR] Nenhum endereco encontrado no HTML")

                except Exception as e:
                    self.logger.error(f"[ADDR] Erro na extração: {str(e)[:50]}... - continuando sem endereco")
                    address_model = None

            # Salvar empresa completa (coordenadas serão preenchidas depois)
            latitude, longitude, distancia_km = None, None, None
            empresa_id = self.repository.save_empresa(termo_id, site_url, domain, motor_busca,
                                                      address_model, latitude, longitude, distancia_km)
            
            # Criar tarefa de geolocalização se houver endereço
            if address_model and address_model.is_valid():
                endereco_id = self.repository.save_endereco(address_model)
                if endereco_id:
                    self.repository.create_geolocation_task(empresa_id, endereco_id)

            # Salvar e-mails se houver
            if emails:
                domain_email = emails[0].split('@')[1] if emails else domain
                self.repository.save_emails(empresa_id, emails, domain_email)

            # Salvar telefones se houver
            if telefones:
                self.repository.save_telefones(empresa_id, telefones)

            # Atualizar status
            status = 'COLETADO' if (emails or telefones) else 'SEM_DADOS'
            self.repository.update_empresa_status(empresa_id, status, nome_empresa)

            # Salvar na tabela planilha se houver dados (sem distância inicialmente)
            if emails or telefones:
                emails_str = ';'.join(emails) + ';' if emails else ''
                telefones_str = ';'.join([t['formatted'] for t in telefones]) + ';' if telefones else ''
                self.repository.save_to_final_sheet(site_url, emails_str, telefones_str, None)

            return True

        except Exception as e:
            self.logger.error(f"Erro ao salvar empresa: {e}")
            return False

    def update_term_status(self, termo_id: int, status: str):
        """Atualiza status do termo processado"""
        self.repository.update_term_status(termo_id, status)

    def reset_data(self, confirm: bool = False):
        """Reset dos dados coletados"""
        if confirm:
            self.repository.reset_collected_data()
            self.logger.info("✅ Dados resetados - começando do zero")
        else:
            self.logger.info("✅ Continuando de onde parou")

    def export_to_excel(self, custom_path: str = None) -> tuple:
        """Exporta dados para Excel"""
        try:
            if custom_path:
                excel_path = Path(custom_path)
            else:
                excel_path = Path(__file__).parent.parent.parent.parent / "output" / "empresas.xlsx"

            excel_path.parent.mkdir(exist_ok=True)

            count = self.repository.export_to_excel(str(excel_path))
            self.logger.info(f"✅ Excel gerado: {count} registros em {excel_path}")
            return True, count

        except Exception as e:
            self.logger.error(f"Erro ao exportar Excel: {e}")
            return False, 0

    def get_statistics(self) -> dict:
        """Obtém estatísticas do processamento"""
        try:
            with self.repository._get_connection() as conn:
                cursor = conn.cursor()

                # Termos
                cursor.execute("SELECT COUNT(*) FROM TB_TERMOS_BUSCA")
                total_termos = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM TB_TERMOS_BUSCA WHERE STATUS_PROCESSAMENTO = 'CONCLUIDO'")
                termos_concluidos = cursor.fetchone()[0]

                # Empresas
                cursor.execute("SELECT COUNT(*) FROM TB_EMPRESAS")
                total_empresas = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM TB_EMPRESAS WHERE STATUS_COLETA = 'COLETADO'")
                empresas_coletadas = cursor.fetchone()[0]

                # E-mails e telefones
                cursor.execute("SELECT COUNT(*) FROM TB_EMAILS")
                total_emails = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM TB_TELEFONES")
                total_telefones = cursor.fetchone()[0]

                return {
                    'termos_total': total_termos,
                    'termos_concluidos': termos_concluidos,
                    'termos_pendentes': total_termos - termos_concluidos,
                    'empresas_total': total_empresas,
                    'empresas_coletadas': empresas_coletadas,
                    'emails_total': total_emails,
                    'telefones_total': total_telefones,
                    'progresso_pct': round((termos_concluidos / total_termos * 100), 1) if total_termos > 0 else 0
                }

        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas: {e}")
            return None
