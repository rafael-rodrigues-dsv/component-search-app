"""
InitializeDatabaseService
Encapsula o fluxo de inicialização usado no startup e o reset-destructivo solicitado.

Comportamento:
- initialize(): roda o fluxo original de inicialização (InitialLoadApplicationService.run(), ensure zip seed, Dynamic discovery, geolocation, generate terms)
- reset_and_initialize(): limpa as tabelas de dados (preservando TB_CEP_CONFIG e TB_TERMOS_BUSCA) e então chama initialize()

Essa implementação reusa os serviços existentes (InitialLoadApplicationService, DynamicGeographicDiscoveryService,
GeolocationApplicationService, DatabaseApplicationService) sem alterar a lógica deles.
"""
from typing import Dict, Any

from src.infrastructure.repositories.access_repository import AccessRepository
from src.application.services.initial_load_application_service import InitialLoadApplicationService
from src.infrastructure.services.dynamic_geographic_discovery_service import DynamicGeographicDiscoveryService
from src.application.services.geolocation_application_service import GeolocationApplicationService
from src.application.services.database_application_service import DatabaseApplicationService
from src.infrastructure.logging.initial_load_logger import load_logger


class InitializeDatabaseService:
    def __init__(self):
        self._access = AccessRepository()
        self._loader = InitialLoadApplicationService()
        self._db_app = DatabaseApplicationService()

    def _delete_tables_preserve_cep_and_terms(self):
        """Executa DELETE nas tabelas de dados, preservando TB_CEP_CONFIG e TB_TERMOS_BUSCA."""
        conn = self._access._get_connection()
        cursor = conn.cursor()
        # Tabelas que podem ser limpas (não incluir TB_CEP_CONFIG e TB_TERMOS_BUSCA)
        tables_to_clear = [
            "TB_BAIRROS",
            "TB_ZONAS",
            "TB_CIDADES",
            "TB_TERMOS_BUSCA",
            "TB_ENDERECOS",
            "TB_EMPRESAS",
            "TB_EMAILS",
            "TB_TELEFONES",
            "TB_GEOLOCALIZACAO",
            "TB_PLANILHA",
            "TB_CEP_ENRICHMENT"
        ]
        try:
            for t in tables_to_clear:
                try:
                    cursor.execute(f"DELETE FROM {t}")
                except Exception as e:
                    # Log and continue
                    load_logger.warning(f"Falha ao limpar tabela {t}: {e}")
            # Preserve TB_TERMOS_BUSCA rows and statuses (do not modify)
            conn.commit()
        finally:
            try:
                cursor.close()
            except Exception:
                pass

    def initialize(self) -> Dict[str, Any]:
        """Executa o fluxo original de inicialização (sem deletar nada).

        Retorna um dicionário com contadores/resultados.
        """
        results = {'zones': 0, 'base_terms': 0, 'zip_ok': False, 'discovery': None, 'geolocation': None, 'terms_generated': 0}

        # 1) Run initial loader (zones, base terms, ensure cep seed)
        load_logger.info('[LOAD] Iniciando população inicial via InitialLoadApplicationService...')
        run_res = self._loader.run()
        results['zones'] = run_res.get('zones', 0)
        results['base_terms'] = run_res.get('terms', 0)
        results['zip_ok'] = run_res.get('zip_ok', False)

        # 2) Dynamic geographic discovery (uses same algorithm as startup)
        try:
            load_logger.info('[GEO] Iniciando descoberta dinâmica de localizações (cidades/bairros)')
            discovery_svc = DynamicGeographicDiscoveryService()
            discovery_res = discovery_svc.discover_locations_from_config()
            results['discovery'] = discovery_res
            load_logger.info(f"[GEO] Descoberta concluída: {discovery_res.get('total_locations', 0)} locais")
        except Exception as e:
            results['discovery'] = {'error': str(e)}
            load_logger.error(f"[GEO] Falha na descoberta dinâmica: {e}")

        # 3) Geolocation processing
        try:
            load_logger.info('[GEO] Iniciando processamento de geolocalização (GeolocationApplicationService)')
            geo_svc = GeolocationApplicationService()
            geo_res = geo_svc.process_geolocation()
            results['geolocation'] = geo_res
            load_logger.info(f"[GEO] Geolocalização concluída: {geo_res}")
        except Exception as e:
            results['geolocation'] = {'error': str(e)}
            load_logger.error(f"[GEO] Falha no processamento de geolocalização: {e}")

        # 4) Generate search terms
        try:
            load_logger.info('[LOAD] Gerando termos de busca...')
            terms_count = self._db_app.initialize_search_terms()
            results['terms_generated'] = terms_count
            load_logger.info(f"[OK] {terms_count} termos de busca gerados")
        except Exception as e:
            results['terms_generated'] = {'error': str(e)}
            load_logger.error(f"[LOAD] Falha ao gerar termos de busca: {e}")

        return results

    def reset_and_initialize(self) -> Dict[str, Any]:
        """Limpa as tabelas (preservando TB_CEP_CONFIG e TB_TERMOS_BUSCA) e executa initialize()."""
        load_logger.info('[LOAD] Executando reset destrutivo (preservando TB_CEP_CONFIG e TB_TERMOS_BUSCA)')
        self._delete_tables_preserve_cep_and_terms()
        load_logger.info('[LOAD] Reset concluído, iniciando initialize()')
        return self.initialize()
