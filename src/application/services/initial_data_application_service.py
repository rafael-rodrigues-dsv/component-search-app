from src.infrastructure.repositories.zone_repository import ZoneRepository
from src.application.services.zip_code_application_service import ZipCodeApplicationService
from src.application.services.search_term_application_service import SearchTermApplicationService
from src.infrastructure.config.config_manager import ConfigManager
from src.infrastructure.logging.initial_load_logger import load_logger


class InitialDataApplicationService:
    """Service responsible for populating initial data after DB tables are created.

    This implementation uses application services (not direct AccessRepository) so the
    main bootstrap stays at service/application layer.
    """

    def __init__(self):
        self.zone_repo = ZoneRepository()
        self.zip_svc = ZipCodeApplicationService()
        self.term_service = SearchTermApplicationService()

    def populate_zones(self) -> int:
        # Try to determine UF from configured reference CEP (via service)
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
        cfg = ConfigManager()
        is_test = cfg.is_test_mode

        # Determine base terms from config.settings - if import fails, raise
        try:
            from config.settings import BASE_BUSCA, BASE_TESTES
        except Exception as e:
            load_logger.error(f"Erro ao carregar config.settings: {e}")
            # raise to avoid using a silent hardcoded fallback
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
