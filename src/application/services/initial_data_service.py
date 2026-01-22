from src.infrastructure.repositories.zone_repository import ZoneRepository
from src.application.services.zip_code_service import ZipCodeService
from src.infrastructure.repositories.search_term_repository import SearchTermRepository
from config.settings import BASE_BUSCA, BASE_TESTES
from src.infrastructure.config.config_manager import ConfigManager
from src.infrastructure.logging.initial_load_logger import load_logger


class InitialDataService:
    """Service responsible for populating initial data after DB tables are created."""

    def __init__(self):
        self.zone_repo = ZoneRepository()
        self.zip_svc = ZipCodeService()
        self.term_repo = SearchTermRepository()

    def populate_zones(self) -> int:
        zones = [
            {'nome': 'zona norte', 'uf': 'SP', 'ativo': True},
            {'nome': 'zona sul', 'uf': 'SP', 'ativo': True},
            {'nome': 'zona leste', 'uf': 'SP', 'ativo': True},
            {'nome': 'zona oeste', 'uf': 'SP', 'ativo': True},
            {'nome': 'zona central', 'uf': 'SP', 'ativo': True},
        ]
        inserted = self.zone_repo.insert_zones(zones)
        load_logger.info(f"Zonas inseridas: {inserted}")
        return inserted

    def populate_base_terms(self) -> int:
        cfg = ConfigManager()
        is_test = cfg.is_test_mode
        base = BASE_TESTES if is_test else BASE_BUSCA
        count = 0
        load_logger.info(f"Populando termos base (is_test={is_test})...")
        # Verificação prévia: confirmar que a tabela TB_BASE_BUSCA existe e que a conexão ODBC funciona
        try:
            # usar execute_query para retornar um dicionário com COUNT
            test = self.term_repo.access.execute_query("SELECT COUNT(*) as cnt FROM TB_BASE_BUSCA")
            if isinstance(test, list) and len(test) > 0:
                load_logger.debug(f"Verificação TB_BASE_BUSCA: {test[0].get('cnt')}")
            else:
                load_logger.warning("Verificação TB_BASE_BUSCA retornou vazio/inválido. Pode haver problemas de conexão ou a tabela não existe.")
        except Exception as e:
            load_logger.error(f"Falha ao validar TB_BASE_BUSCA antes da inserção: {e}")
            return 0
        for term in base:
            try:
                self.term_repo.insert_term(term, categoria='elevadores', is_test=is_test)
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
