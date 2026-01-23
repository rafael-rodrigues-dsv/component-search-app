"""
Initial load runner service
This service encapsulates the logic that previously lived in `main.py` to populate
initial data (zones, base terms and ensure TB_CEP_CONFIG seed) so the application
entrypoint remains thin and the logic is testable and reusable.
"""
from typing import Dict

from src.infrastructure.logging.initial_load_logger import load_logger
from src.infrastructure.config.config_manager import ConfigManager
from src.infrastructure.repositories.zone_repository import ZoneRepository
from src.application.services.zip_code_application_service import ZipCodeApplicationService
from src.application.services.search_term_application_service import SearchTermApplicationService


class InitialLoadApplicationService:
    """Runner service that orchestrates initial population steps.

    This class centralizes the initial data population logic that used to live in
    `InitialDataApplicationService` and scripts/load_initial_data.py. It is intended
    to be the single entry point for seeding zones, base terms and ensuring the
    TB_CEP_CONFIG seed.
    """

    def __init__(self) -> None:
        self.zone_repo = ZoneRepository()
        self.zip_svc = ZipCodeApplicationService()
        self.term_service = SearchTermApplicationService()
        self.config = ConfigManager()

    def populate_zones(self) -> int:
        """Populate TB_ZONAS based on the UF derived from the reference CEP."""
        try:
            cep_row = self.zip_svc.get_reference_cep()
        except Exception as e:
            load_logger.error(f"Falha ao obter CEP de referência para determinar UF das zonas: {e}")
            raise

        if not cep_row or not cep_row.get('estado'):
            raise RuntimeError('UF de referência não encontrado (TB_CEP_CONFIG) - não é possível popular zonas')

        uf = cep_row.get('estado')

        zones = [
            {'nome': 'zona norte', 'uf': uf, 'ativo': True},
            {'nome': 'zona sul', 'uf': uf, 'ativo': True},
            {'nome': 'zona leste', 'uf': uf, 'ativo': True},
            {'nome': 'zona oeste', 'uf': uf, 'ativo': True},
            {'nome': 'zona central', 'uf': uf, 'ativo': True},
        ]
        inserted = self.zone_repo.insert_zones(zones)
        load_logger.info(f"Zonas inseridas: {inserted} (UF={uf})")
        return inserted

    def populate_base_terms(self) -> int:
        """Populate TB_BASE_BUSCA with base terms depending on is_test mode."""
        is_test = self.config.is_test_mode

        # Determine base terms from config.settings - if import fails, raise
        try:
            from config.settings import BASE_BUSCA, BASE_TESTES
        except Exception as e:
            load_logger.error(f"Erro ao carregar config.settings: {e}")
            raise

        base = BASE_TESTES if is_test else BASE_BUSCA
        count = 0
        load_logger.info(f"Populando termos base (is_test={is_test})...")

        # Try a light validation that the table exists by delegating to repository count via service
        try:
            total_existing = self.term_service.repo.count_active_terms()
            load_logger.debug(f"Verificação TB_BASE_BUSCA: {total_existing} registros ativos existentes")
        except Exception as e:
            load_logger.error(f"Falha ao validar TB_BASE_BUSCA antes da inserção: {e}")
            return 0

        for term in base:
            try:
                self.term_service.insert_term(term, categoria='elevadores', is_test=is_test)
                count += 1
                load_logger.debug(f"Inserido termo: {term}")
            except Exception as e:
                load_logger.warning(f"Falha ao inserir termo '{term}': {e}")
        load_logger.info(f"Total termos inseridos: {count}")
        return count

    def ensure_zip_seed(self) -> bool:
        load_logger.info("Garantindo TB_CEP_CONFIG e seed (se necessário)...")
        ok = self.zip_svc.ensure_table_and_seed()
        if ok:
            load_logger.info("TB_CEP_CONFIG garantida/seed aplicada")
        else:
            load_logger.warning("Não foi possível garantir TB_CEP_CONFIG via ZipCodeService")
        return ok

    def run(self) -> Dict[str, object]:
        """Execute the initial population steps.

        Returns a dict with results keys: zones, terms, zip_ok
        Raises any exception encountered after logging full traceback.
        """
        try:
            load_logger.info('Iniciando população inicial via InitialLoadApplicationService...')

            zones_count = self.populate_zones()
            load_logger.info(f'Zonas populadas: {zones_count}')

            terms_count = self.populate_base_terms()
            load_logger.info(f'Termos base populados: {terms_count}')

            zip_ok = self.ensure_zip_seed()
            load_logger.info(f'TB_CEP_CONFIG garantida/seed: {zip_ok}')

            return {
                'zones': zones_count,
                'terms': terms_count,
                'zip_ok': zip_ok
            }

        except Exception:
            # Log full stacktrace for debugging
            import traceback
            tb = traceback.format_exc()
            try:
                load_logger.error(f'Falha na população inicial: {tb}')
            except Exception:
                print(f"[ERRO] Falha na população inicial: {tb}")
            raise

    # Backwards-compatible helper to support scripts that called initialize_database()
    def initialize_database(self) -> None:
        """Backward-compatible wrapper used by the deploy script.

        Prints brief status messages to stdout then delegates to run().
        """
        print("[INFO] Inicializando banco de dados via InitialLoadApplicationService...")
        results = self.run()
        print(f"[OK] Inicialização concluída. Zonas: {results.get('zones')}, Termos: {results.get('terms')}, CEP seed: {results.get('zip_ok')}")

