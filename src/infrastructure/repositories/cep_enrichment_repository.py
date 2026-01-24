"""
Repository for TB_CEP_ENRICHMENT
"""
from typing import List, Dict
import logging
from src.infrastructure.repositories.access_repository import AccessRepository
import threading

class CepEnrichmentRepository:
    def __init__(self):
        self._access = AccessRepository()
        self._logger = logging.getLogger(__name__)

    def create_task(self, empresa_id: int, endereco_id: int):
        if not endereco_id:
            return
        try:
            conn = self._access._get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT ID_CEP_ENRICHMENT FROM TB_CEP_ENRICHMENT WHERE ID_EMPRESA = ?", (empresa_id,))
                existing = cursor.fetchone()
                if not existing:
                    cursor.execute(
                        "INSERT INTO TB_CEP_ENRICHMENT (ID_EMPRESA, ID_ENDERECO, STATUS_PROCESSAMENTO, TENTATIVAS) VALUES (?, ?, 'PENDENTE', 0)",
                        (empresa_id, endereco_id)
                    )
                    conn.commit()
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass
        except Exception as e:
            self._logger.exception(f"create_task failed for empresa_id={empresa_id} endereco_id={endereco_id}: {e}")

    def _execute_select_with_timeout(self, query: str, params: tuple = None, timeout: float = 5.0):
        """Execute a SELECT query in a worker thread and return rows or None on timeout/error."""
        from typing import Dict, Any
        result_container: Dict[str, Any] = {'rows': None, 'error': None}

        def worker():
            try:
                conn = self._access._get_connection()
                cursor = conn.cursor()
                try:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    rows = cursor.fetchall()
                    result_container['rows'] = rows
                finally:
                    try:
                        cursor.close()
                    except Exception:
                        pass
            except Exception as e:
                result_container['error'] = e
                # Also print to stderr for immediate visibility
                try:
                    print(f"[CEP-REPO] Exception during DB worker: {e}")
                except Exception:
                    pass

        th = threading.Thread(target=worker, daemon=True)
        th.start()
        th.join(timeout)
        if th.is_alive():
            msg = f"[CEP-REPO] Query timeout after {timeout}s"
            try:
                print(msg)
            except Exception:
                pass
            self._logger.error(f"Query timeout after {timeout}s: {query[:200]}")
            return None
        if result_container.get('error'):
            try:
                print(f"[CEP-REPO] Query execution error: {result_container['error']}")
            except Exception:
                pass
            self._logger.exception(f"Query execution error: {result_container['error']}")
            return None
        return result_container.get('rows')

    def fetch_pending(self) -> List[Dict]:
        try:
            query = (
                """
                SELECT c.ID_CEP_ENRICHMENT, c.ID_EMPRESA, c.ID_ENDERECO, emp.SITE_URL,
                       end.LOGRADOURO, end.NUMERO, end.COMPLEMENTO, end.BAIRRO, end.CIDADE, end.ESTADO, end.CEP
                FROM (TB_CEP_ENRICHMENT c 
                INNER JOIN TB_EMPRESAS emp ON c.ID_EMPRESA = emp.ID_EMPRESA)
                INNER JOIN TB_ENDERECOS end ON c.ID_ENDERECO = end.ID_ENDERECO
                WHERE c.STATUS_PROCESSAMENTO = 'PENDENTE'
                ORDER BY c.ID_CEP_ENRICHMENT
                """
            )
            rows = self._execute_select_with_timeout(query, params=None, timeout=8.0)
            if rows is None:
                # timed out or error
                return []

            tasks = []
            for row in rows:
                from src.domain.models.address_model import AddressModel
                address = AddressModel(
                    logradouro=row[4] or "",
                    numero=row[5] or "",
                    complemento=row[6] or "",
                    bairro=row[7] or "",
                    cidade=row[8] or "",
                    estado=row[9] or "",
                    cep=row[10] or ""
                )
                tasks.append({
                    'id_cep_enrichment': row[0],
                    'id_empresa': row[1],
                    'id_endereco': row[2],
                    'site_url': row[3],
                    'address_model': address
                })
            return tasks
        except Exception as e:
            self._logger.exception(f"fetch_pending failed: {e}")
            return []

    def update_success(self, id_cep_enrichment: int):
        try:
            conn = self._access._get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE TB_CEP_ENRICHMENT SET STATUS_PROCESSAMENTO = 'CONCLUIDO', DATA_PROCESSAMENTO = Date(), TENTATIVAS = TENTATIVAS + 1 WHERE ID_CEP_ENRICHMENT = ?",
                    (id_cep_enrichment,)
                )
                conn.commit()
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass
        except Exception as e:
            self._logger.exception(f"update_success failed for id={id_cep_enrichment}: {e}")

    def update_error(self, id_cep_enrichment: int, erro_descricao: str):
        try:
            conn = self._access._get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "UPDATE TB_CEP_ENRICHMENT SET STATUS_PROCESSAMENTO = 'ERRO', DATA_PROCESSAMENTO = Date(), TENTATIVAS = TENTATIVAS + 1, ERRO_DESCRICAO = ? WHERE ID_CEP_ENRICHMENT = ?",
                    (erro_descricao, id_cep_enrichment)
                )
                conn.commit()
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass
        except Exception as e:
            self._logger.exception(f"update_error failed for id={id_cep_enrichment}: {e}")

    def stats(self) -> Dict[str, int]:
        # Use a single query with SUM(IIF(...)) to be robust on Access and run with timeout
        try:
            query = (
                "SELECT "
                "SUM(IIF(STATUS_PROCESSAMENTO='CONCLUIDO',1,0)) AS CONCL, "
                "SUM(IIF(STATUS_PROCESSAMENTO='PENDENTE',1,0)) AS PEND, "
                "SUM(IIF(STATUS_PROCESSAMENTO='ERRO',1,0)) AS ERROS "
                "FROM TB_CEP_ENRICHMENT"
            )
            rows = self._execute_select_with_timeout(query, params=None, timeout=6.0)
            if not rows:
                return {'total': 0, 'concluidos': 0, 'pendentes': 0, 'erros': 0, 'percentual': 0}
            row = rows[0]
            concluidos = int(row[0] or 0)
            pendentes = int(row[1] or 0)
            erros = int(row[2] or 0)
            total = concluidos + pendentes + erros
            percentual = round((concluidos / max(total, 1)) * 100, 1)
            return {
                'total': total,
                'concluidos': concluidos,
                'pendentes': pendentes,
                'erros': erros,
                'percentual': percentual
            }
        except Exception as e:
            self._logger.exception(f"stats failed (fallback): {e}")
            return {'total': 0, 'concluidos': 0, 'pendentes': 0, 'erros': 0, 'percentual': 0}

    def fetch_all(self, query: str) -> List[tuple]:
        """Execute an arbitrary SELECT query and return list of rows as tuples."""
        rows = self._execute_select_with_timeout(query, params=None, timeout=8.0)
        if rows is None:
            return []
        return rows

    # --- NEW: model pagination helpers ---
    def fetch_models_paginated(self, limit: int = 10, offset: int = 0):
        from src.domain.models.cep_enrichment_model import CepEnrichmentModel
        # Parse strictly
        limit = int(limit) if limit else 10
        offset = int(offset) if offset else 0
        sql = "SELECT ID_CEP_ENRICHMENT AS id_cep_enrichment, ID_EMPRESA AS id_empresa, ID_ENDERECO AS id_endereco, STATUS_PROCESSAMENTO AS status, TENTATIVAS FROM TB_CEP_ENRICHMENT ORDER BY ID_CEP_ENRICHMENT"
        rows = self._access.execute_query(sql, None)
        models = []
        for r in rows[offset: offset + limit]:
            try:
                models.append(CepEnrichmentModel.from_row(r))
            except Exception:
                continue
        return models

    def count(self) -> int:
        try:
            rows = self._access.execute_query("SELECT COUNT(*) as cnt FROM TB_CEP_ENRICHMENT")
            if isinstance(rows, list) and rows:
                return int(rows[0].get('cnt', 0) or 0)
            return 0
        except Exception:
            return 0

