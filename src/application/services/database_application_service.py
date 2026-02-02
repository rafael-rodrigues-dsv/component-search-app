"""
Serviço de aplicação para gerenciamento do banco de dados
"""
import logging
from pathlib import Path

from ...domain.services.database_domain_service import DatabaseDomainService


class DatabaseApplicationService:
    """Serviço para operações de banco de dados"""

    def __init__(self):
        self.domain_service = DatabaseDomainService()
        self.logger = logging.getLogger(__name__)
        # Source of last-initialized terms: 'db', 'base_testes', 'base_busca', 'static_fallback'
        self.last_terms_source = None

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
                # If terms already existed, mark source as 'db'
                self.last_terms_source = 'db'
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
            self.last_terms_source = 'static_fallback'
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
            
            # Verificar modo de teste
            is_test_mode = config.is_test_mode
            print(f"[INFO] Modo de execução: {'TESTE' if is_test_mode else 'PRODUÇÃO'}")

            # Tentar obter termos do banco (TB_BASE_BUSCA)
            base_busca = None
            try:
                from .search_term_application_service import SearchTermApplicationService
                st_service = SearchTermApplicationService()
                # Obter todos os termos ativos (independente do modo teste)
                active_rows = st_service.get_active_terms(is_test=False)
                print(f"[INFO] Encontrados {len(active_rows)} termos na TB_BASE_BUSCA")

                if active_rows:
                    # Extrair apenas o texto dos termos
                    active_terms = []
                    for r in active_rows:
                        termo = r.get('TERMO_BUSCA') or r.get('termo_busca') or r.get('TERMO') or r.get('termo')
                        if termo:
                            active_terms.append(termo)

                    if active_terms:
                        base_busca = active_terms
                        print(f"[INFO] ✅ Usando {len(base_busca)} termos ativos da TB_BASE_BUSCA: {base_busca}")
                        self.last_terms_source = 'db'
                    else:
                        print("[AVISO] Nenhum termo válido encontrado na TB_BASE_BUSCA")
            except Exception as e:
                print(f"[AVISO] Erro ao ler termos da TB_BASE_BUSCA: {e}")
                import traceback
                print(traceback.format_exc())

            # Fallback para constants do settings se não encontrou termos no banco
            if not base_busca:
                from config.settings import BASE_BUSCA, BASE_TESTES
                if is_test_mode:
                    print("[INFO] ⚠️  Fallback para BASE_TESTES do config/settings.py")
                    base_busca = BASE_TESTES
                    self.last_terms_source = 'base_testes'
                else:
                    print("[INFO] ⚠️  Fallback para BASE_BUSCA do config/settings.py")
                    base_busca = BASE_BUSCA
                    self.last_terms_source = 'base_busca'

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
                neighborhood_name = neighborhood['name']
                city_name = neighborhood.get('city', '')

                # ⚠️ SKIP: Se bairro tem o mesmo nome da cidade, não gera termo (evita duplicação com CIDADE)
                if city_name and neighborhood_name.strip().lower() == city_name.strip().lower():
                    continue

                for categoria in base_busca:
                    # Concatenar cidade ao bairro se o nome da cidade não estiver no nome do bairro
                    # Verificar se o nome da cidade já está no nome do bairro (case-insensitive)
                    if city_name and city_name.lower() not in neighborhood_name.lower():
                        # Cidade não está no nome do bairro, então concatena
                        location_text = f"{neighborhood_name} {city_name}"
                    else:
                        # Cidade já está no nome ou não há cidade definida
                        location_text = neighborhood_name

                    termo = f"{categoria} {location_text}"
                    terms.append({
                        'id': term_id,
                        'termo': termo,
                        'localizacao': location_text,  # Salvar com cidade concatenada
                        'tipo_localizacao': 'BAIRRO',
                        'cidade_pai': city_name,
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
        try:
            rows = self.domain_service.get_pending_terms()
            # Normalize DB column names (Access returns uppercase column names) to a simple dict shape
            normalized = []
            for r in rows or []:
                # r may be dict with keys like ID_TERMO, TERMO_COMPLETO, TIPO_LOCALIZACAO, STATUS_PROCESSAMENTO
                row = {}
                # id
                if 'ID_TERMO' in r:
                    row['id'] = r.get('ID_TERMO')
                elif 'id' in r:
                    row['id'] = r.get('id')
                else:
                    row['id'] = r.get('ID') or r.get('Id')
                # termo
                if 'TERMO_COMPLETO' in r:
                    row['termo'] = r.get('TERMO_COMPLETO')
                elif 'TERMO_BUSCA' in r:
                    row['termo'] = r.get('TERMO_BUSCA')
                else:
                    row['termo'] = r.get('termo') or r.get('TERMO')
                # tipo_localizacao
                if 'TIPO_LOCALIZACAO' in r:
                    row['tipo_localizacao'] = r.get('TIPO_LOCALIZACAO')
                else:
                    row['tipo_localizacao'] = r.get('tipo_localizacao') or r.get('tipo')
                # status
                if 'STATUS_PROCESSAMENTO' in r:
                    row['status'] = r.get('STATUS_PROCESSAMENTO')
                else:
                    row['status'] = r.get('status')

                normalized.append(row)

            # If there are no pending terms, attempt a fallback to base active terms (TB_BASE_BUSCA)
            if not normalized:
                try:
                    from .search_term_application_service import SearchTermApplicationService
                    from ...infrastructure.config.config_manager import ConfigManager
                    cfg = ConfigManager()
                    st_service = SearchTermApplicationService()
                    active = st_service.get_active_terms(is_test=cfg.is_test_mode)
                    fallback = []
                    for a in active:
                        # a may contain TERMO_BUSCA or TERMO
                        term_text = a.get('TERMO_BUSCA') if isinstance(a, dict) else a
                        if not term_text:
                            term_text = a.get('TERMO') if isinstance(a, dict) else term_text
                        fallback.append({'id': a.get('ID_BASE') if isinstance(a, dict) else None, 'termo': term_text, 'tipo_localizacao': '', 'status': 'PENDENTE'})
                    if fallback:
                        return fallback
                except Exception:
                    pass

            return normalized
        except Exception as e:
            self.logger.error(f"Erro ao obter termos de busca: {e}")
            return []

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
            # Retornar dict padrão para evitar None
            return {
                'termos_total': 0,
                'termos_concluidos': 0,
                'progresso_pct': 0,
                'empresas_total': 0,
                'empresas_visitadas': 0,
                'empresas_coletadas': 0,
                'empresas_nao_coletadas': 0,
                'taxa_coleta_pct': 0,
                'emails_total': 0,
                'telefones_total': 0
            }

    def get_company_collection_stats(self) -> dict:
        """Obtém estatísticas detalhadas de coleta de empresas"""
        try:
            return self.domain_service.get_company_collection_statistics()
        except Exception as e:
            self.logger.error(f"Erro ao obter estatísticas de empresas: {e}")
            return {'visitadas': 0, 'coletadas': 0, 'nao_coletadas': 0, 'taxa_coleta_pct': 0}
