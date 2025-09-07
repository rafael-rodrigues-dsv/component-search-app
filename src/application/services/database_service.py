"""
Serviço de aplicação para gerenciamento do banco de dados
"""
import logging
from pathlib import Path

from ...domain.services.database_domain_service import DatabaseDomainService


class DatabaseService:
    """Serviço para operações de banco de dados"""

    def __init__(self):
        self.domain_service = DatabaseDomainService()
        self.logger = logging.getLogger(__name__)

    def initialize_search_terms(self) -> int:
        """Inicializa termos de busca dinamicamente (só se necessário)"""
        try:
            from ...infrastructure.config.config_manager import ConfigManager
            from ...infrastructure.services.dynamic_geographic_discovery_service import DynamicGeographicDiscoveryService
            
            config = ConfigManager()
            
            # Verificar se descoberta dinâmica está habilitada
            if not config.geographic_discovery_enabled:
                return self._initialize_static_terms()
            
            # Verificar se já existem termos no banco (pendentes ou concluídos)
            total_terms = self.domain_service.count_total_search_terms()
            if total_terms > 0:
                pending_terms = self.domain_service.get_pending_terms()
                print(f"[INFO] {total_terms} termos já existem ({len(pending_terms)} pendentes) - pulando descoberta dinâmica")
                return len(pending_terms) if pending_terms else total_terms
            
            print("[INFO] Nenhum termo encontrado - executando descoberta dinâmica...")
            
            # Descobrir localizações dinamicamente
            discovery_service = DynamicGeographicDiscoveryService()
            locations = discovery_service.discover_locations_from_config()
            
            # Gerar termos
            terms_count = self._generate_terms_from_locations(locations)
            print(f"[OK] {terms_count} termos gerados dinamicamente")
            
            return terms_count
            
        except Exception as e:
            self.logger.error(f"Erro na descoberta dinâmica: {e}")
            print(f"[ERRO] Falha na descoberta dinâmica: {e}")
            print("[INFO] Usando método estático como fallback...")
            return self._initialize_static_terms()
    

    
    def _initialize_static_terms(self) -> int:
        """Método estático original (fallback)"""
        try:
            pending_terms = self.domain_service.get_pending_terms()

            if not pending_terms:
                self.logger.info("Gerando termos de busca estáticos...")
                count = 0  # Método estático removido
                self.logger.info(f"✅ {count} termos de busca gerados")
                return count
            else:
                self.logger.info(f"✅ {len(pending_terms)} termos já existem")
                return len(pending_terms)

        except Exception as e:
            self.logger.error(f"Erro ao inicializar termos estáticos: {e}")
            return 0
    
    def _generate_terms_from_locations(self, locations: dict) -> int:
        """Gera termos de busca a partir das localizações descobertas"""
        try:
            from ...infrastructure.config.config_manager import ConfigManager
            config = ConfigManager()
            
            # Limpar termos existentes
            self.domain_service.clear_search_terms()
            
            # Verificar modo de teste e usar constantes do config
            is_test_mode = config.is_test_mode
            
            from config.settings import BASE_BUSCA, BASE_TESTES
            
            if is_test_mode:
                print("[INFO] Modo TESTE ativado - usando base reduzida")
                base_busca = BASE_TESTES
            else:
                print("[INFO] Modo PRODUÇÃO ativado - usando base completa")
                base_busca = BASE_BUSCA
            
            terms = []
            term_id = 1
            
            # Gerar termos para cidades
            for city in locations.get('cities', []):
                for categoria in base_busca:
                    termo = f"{categoria} {city['name']}"
                    terms.append({
                        'id': term_id,
                        'termo': termo,
                        'localizacao': city['name'],
                        'tipo_localizacao': 'CIDADE',
                        'distancia_km': city['distance_km'],
                        'status': 'PENDENTE'
                    })
                    term_id += 1
            
            # Gerar termos para bairros
            for neighborhood in locations.get('neighborhoods', []):
                for categoria in base_busca:
                    termo = f"{categoria} {neighborhood['name']}"
                    terms.append({
                        'id': term_id,
                        'termo': termo,
                        'localizacao': neighborhood['name'],
                        'tipo_localizacao': 'BAIRRO',
                        'cidade_pai': neighborhood.get('city'),
                        'distancia_km': neighborhood['distance_km'],
                        'status': 'PENDENTE'
                    })
                    term_id += 1
            
            # Salvar termos no banco
            count = self.domain_service.save_dynamic_search_terms(terms)
            return count
            
        except Exception as e:
            self.logger.error(f"Erro ao gerar termos dinâmicos: {e}")
            return 0

    def get_search_terms(self) -> list:
        """Obtém lista de termos para processamento"""
        return self.domain_service.get_pending_terms()

    def is_domain_visited(self, domain: str) -> bool:
        """Verifica se domínio já foi visitado"""
        return self.domain_service.is_domain_visited(domain)

    def is_email_collected(self, email: str) -> bool:
        """Verifica se e-mail já foi coletado"""
        return self.domain_service.is_email_collected(email)

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
            # Usar Domain Service para salvar empresa
            return self.domain_service.save_company_data(termo_id, site_url, domain, motor_busca,
                                                         emails, telefones, nome_empresa, html_content)

        except Exception as e:
            self.logger.error(f"Erro ao salvar empresa: {e}")
            return False

    def update_term_status(self, termo_id: int, status: str):
        """Atualiza status do termo processado"""
        self.domain_service.update_term_status(termo_id, status)

    def reset_data(self, confirm: bool = False):
        """Reset dos dados coletados"""
        if confirm:
            self.domain_service.reset_collected_data()
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

            count = self.domain_service.export_to_excel(str(excel_path))
            self.logger.info(f"✅ Excel gerado: {count} registros em {excel_path}")
            return True, count

        except Exception as e:
            self.logger.error(f"Erro ao exportar Excel: {e}")
            return False, 0

    def get_statistics(self) -> dict:
        """Obtém estatísticas do processamento"""
        try:
            return self.domain_service.get_processing_statistics()
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas: {e}")
            return None
