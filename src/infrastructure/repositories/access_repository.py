"""
Repositório para acesso ao banco Access - agora reduzido a helpers de conexão/executor.
As operações específicas de tabela devem ser realizadas pelos repositórios dedicados
(ex.: CompaniesRepository, AddressesRepository, EmailsRepository, PhonesRepository,
TermsRepository, GeolocationRepository, CepEnrichmentRepository, etc.).
"""
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple

import pyodbc
import threading


class AccessRepository:
    """Repositório principal para banco Access (reduzido)

    Responsabilidade atual:
    - prover conexão singleton
    - executar queries genéricas (execute_query/fetch_scalar/fetch_one)
    - delegar operações complexas para repositórios dedicados (fora daqui)
    """

    # NOTE: avoid sharing a single pyodbc connection across threads (pyodbc connections are not thread-safe).
    # Use thread-local connections so each thread gets its own connection instance.
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        project_root = Path.cwd()
        self.db_path = project_root / "data" / "pythonsearch.accdb"
        self.db_path = self.db_path.resolve()
        self.conn_str = f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.db_path};'
        self.logger = logging.getLogger(__name__)
        # Thread-local storage for per-thread connections
        self._local = threading.local()
        self._initialized = True

    def _get_connection(self):
        """Obtém conexão singleton com o banco"""
        import time
        # Use a connection per thread to avoid pyodbc cross-thread issues
        conn = getattr(self._local, 'connection', None)
        if conn is None:
            attempts = 6
            delay = 0.2
            last_exc = None
            for attempt in range(1, attempts + 1):
                try:
                    conn = pyodbc.connect(self.conn_str)
                    # Enable autocommit to avoid leaving transactions open which can lock the file
                    try:
                        conn.autocommit = True
                    except Exception:
                        # Some pyodbc/driver versions may not expose autocommit attribute
                        pass
                    # store on thread-local
                    self._local.connection = conn
                    return conn
                except Exception as e:
                    last_exc = e
                    self.logger.warning(f"Tentativa {attempt}/{attempts} - falha ao conectar ODBC: {e}")
                    if attempt < attempts:
                        time.sleep(delay)
                        delay *= 2
                        continue
                    raise
        return conn

    def close_connection(self):
        """Fecha conexão singleton"""
        # Close thread-local connection for the current thread
        conn = getattr(self._local, 'connection', None)
        if conn:
            try:
                conn.close()
            except Exception:
                pass
            try:
                del self._local.connection
            except Exception:
                pass

    def execute_query(self, query: str, params: list = None):
        """Executa uma query SQL. Para SELECT retorna lista de dicts {col: value}.
        Para INSERT/UPDATE/DELETE executa e commita, retornando lista vazia.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
        except Exception as e:
            self.logger.debug(f"execute_query SQL error: {e} - Query: {query} Params: {params}")
            raise

        columns = None
        try:
            columns = [col[0] for col in cursor.description] if cursor.description else None
        except Exception:
            columns = None

        if columns:
            rows = cursor.fetchall()
            result = []
            for row in rows:
                row_vals = list(row)
                obj = {columns[i]: row_vals[i] for i in range(len(columns))}
                result.append(obj)
            return result
        else:
            try:
                conn.commit()
            except Exception:
                pass
            return []

    def fetch_scalar(self, query: str, params: list = None):
        """Executa uma query SELECT e retorna o primeiro valor (primeira coluna da primeira linha)"""
        rows = self.execute_query(query, params)
        if not rows:
            return None
        first = rows[0]
        if isinstance(first, dict):
            return next(iter(first.values()))
        return None

    def fetch_one(self, query: str, params: list = None):
        """Executa uma query e retorna a primeira linha como tupla (ou None)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            row = cursor.fetchone()
            try:
                cursor.close()
            except Exception:
                pass
            return row
        except Exception:
            try:
                cursor.close()
            except Exception:
                pass
            raise

    # NOTE: The table-specific operations that used to live here were moved to dedicated
    # repositories to follow single responsibility. If you previously called these
    # methods on an AccessRepository instance, update code to use the specific repository
    # class, for example:
    #   from src.infrastructure.repositories.companies_repository import CompaniesRepository
    #   repo = CompaniesRepository()
    #   repo.is_domain_visited(domain)

    # The AccessRepository remains intentionally minimal.

    # ===== RESET (kept) =====
    def reset_collected_data(self):
        """Limpa dados coletados delegando a MaintenanceRepository (centraliza operações multi-tabela)."""
        try:
            from src.infrastructure.repositories.maintenance_repository import MaintenanceRepository
            repo = MaintenanceRepository()
            return repo.reset_collected_data()
        except Exception:
            try:
                conn = self._get_connection()
                cursor = conn.cursor()
                tables = [
                    "TB_CEP_ENRICHMENT",
                    "TB_GEOLOCALIZACAO",
                    "TB_TELEFONES",
                    "TB_EMAILS",
                    "TB_EMPRESAS",
                    "TB_PLANILHA"
                ]
                for table in tables:
                    cursor.execute(f"DELETE FROM {table}")
                cursor.execute("UPDATE TB_TERMOS_BUSCA SET STATUS_PROCESSAMENTO = 'PENDENTE', DATA_PROCESSAMENTO = NULL")
                from src.infrastructure.repositories.terms_repository import TermsRepository
                tr = TermsRepository()
                tr.delete_all()
                conn.commit()
                try:
                    cursor.close()
                except Exception:
                    pass
            except Exception:
                pass

    # ===== AGGREGATED STATS (kept) =====
    def get_processing_statistics(self) -> Dict[str, int]:
        """Delegate aggregated statistics to StatisticsRepository."""
        try:
            from src.infrastructure.repositories.statistics_repository import StatisticsRepository
            repo = StatisticsRepository()
            return repo.get_processing_statistics()
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
        """Delegate company collection statistics to CompaniesRepository."""
        try:
            from src.infrastructure.repositories.companies_repository import CompaniesRepository
            repo = CompaniesRepository()
            return repo.get_collection_statistics()
        except Exception:
            return {'visitadas': 0, 'coletadas': 0, 'nao_coletadas': 0, 'taxa_coleta_pct': 0}

# End of AccessRepository - heavy SQL implementations moved to dedicated repositories.

