"""
Repositório para gerenciamento de termos de busca (TB_BASE_BUSCA)
"""
from typing import List, Dict, Any
from .access_repository import AccessRepository


class SearchTermRepository:
    def __init__(self):
        self.access = AccessRepository()

    def list_active_terms(self, is_test: bool = False) -> List[Dict[str, Any]]:
        try:
            query = "SELECT ID_BASE, TERMO_BUSCA, CATEGORIA, ATIVO, DATA_CRIACAO FROM TB_BASE_BUSCA WHERE ATIVO = -1 ORDER BY ID_BASE"
            return self.access.execute_query(query)
        except Exception as e:
            # Log via access repository (executor) ou print para facilitar debug
            try:
                from src.infrastructure.logging.initial_load_logger import load_logger
                load_logger.error(f"Erro listando termos ativos: {e}")
            except Exception:
                pass
            return []

    def insert_term(self, termo: str, categoria: str = 'base', is_test: bool = False) -> int:
        # Instrumented insert with small retry and detailed logging to initial load log
        from src.infrastructure.logging.initial_load_logger import load_logger
        import time, traceback

        attempts = 3
        delay = 0.2
        params = (termo, categoria, -1 if is_test else 0)

        # First, check if the term already exists (case-insensitive match) to avoid duplicates
        try:
            conn = self.access._get_connection()
            cursor = conn.cursor()
            try:
                # Access SQL: use UCase for case-insensitive comparison
                cursor.execute("SELECT ID_BASE FROM TB_BASE_BUSCA WHERE UCase(TERMO_BUSCA) = UCase(?)", (termo,))
                existing = cursor.fetchone()
                if existing and existing[0]:
                    load_logger.debug(f"Termo já existe (retornando ID): {termo} -> {existing[0]}")
                    try:
                        cursor.close()
                    except Exception:
                        pass
                    return existing[0]
            except Exception:
                # se a verificação falhar, prosseguir para tentativa de inserção (retry logic lidará com erros)
                try:
                    cursor.close()
                except Exception:
                    pass

        except Exception:
            # se não conseguir abrir conexão para checar (lock temporário), continuamos para a lógica de retry
            pass

        for attempt in range(1, attempts + 1):
            try:
                load_logger.debug(f"Inserindo termo (attempt {attempt}): {termo} (is_test={is_test})")
                conn = self.access._get_connection()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO TB_BASE_BUSCA (TERMO_BUSCA, CATEGORIA, ATIVO, DATA_CRIACAO, IS_TEST) VALUES (?, ?, -1, Date(), ?)", params)
                cursor.execute("SELECT @@IDENTITY")
                id_base = cursor.fetchone()[0]
                conn.commit()
                try:
                    cursor.close()
                except Exception:
                    pass
                load_logger.debug(f"Inserido termo com ID {id_base}: {termo}")
                return id_base
            except Exception as e:
                load_logger.warning(f"Falha ao inserir termo (attempt {attempt}): {termo} - {e}")
                load_logger.debug(traceback.format_exc())
                if attempt < attempts:
                    time.sleep(delay)
                    delay *= 2
                    continue
                # re-raise to let caller know if all attempts failed
                raise

    def insert_change(self, termo: str, acao: str, target_id: int = None, proposto_por: str = 'user') -> int:
        """Insere uma proposta/alteração — sem tabela de changes: operações aplicadas diretamente em TB_TERMOS_BUSCA.

        - ADD: insere novo termo em TB_TERMOS_BUSCA com STATUS_PROCESSAMENTO='PENDENTE' e retorna ID_TERMO
        - UPDATE: atualiza TERMO_COMPLETO do registro target_id e retorna target_id
        - DELETE: remove (ou marca) o registro target_id e retorna target_id
        """
        conn = self.access._get_connection()
        cursor = conn.cursor()

        try:
            acao = (acao or '').upper()
            if acao == 'ADD':
                cursor.execute("INSERT INTO TB_TERMOS_BUSCA (TERMO_COMPLETO, TIPO_LOCALIZACAO, STATUS_PROCESSAMENTO, DATA_CRIACAO) VALUES (?, ?, 'PENDENTE', Date())", (termo, 'UI'))
                cursor.execute("SELECT @@IDENTITY")
                new_id = cursor.fetchone()[0]
                conn.commit()
                cursor.close()
                return new_id
            elif acao == 'UPDATE' and target_id:
                cursor.execute("UPDATE TB_TERMOS_BUSCA SET TERMO_COMPLETO = ?, DATA_PROCESSAMENTO = NULL, STATUS_PROCESSAMENTO = 'PENDENTE' WHERE ID_TERMO = ?", (termo, target_id))
                conn.commit()
                cursor.close()
                return target_id
            elif acao == 'DELETE' and target_id:
                # Preferir marcar como inativo via STATUS_PROCESSAMENTO = 'REMOVIDO'
                try:
                    cursor.execute("UPDATE TB_TERMOS_BUSCA SET STATUS_PROCESSAMENTO = 'REMOVIDO', DATA_PROCESSAMENTO = Date() WHERE ID_TERMO = ?", (target_id,))
                except Exception:
                    # fallback para exclusão física
                    cursor.execute("DELETE FROM TB_TERMOS_BUSCA WHERE ID_TERMO = ?", (target_id,))
                conn.commit()
                cursor.close()
                return target_id
            else:
                cursor.close()
                return -1
        except Exception:
            try:
                cursor.close()
            except Exception:
                pass
            return -1

    def list_pending_changes(self) -> List[Dict[str, Any]]:
        """Lista termos pendentes diretamente da TB_TERMOS_BUSCA (STATUS_PROCESSAMENTO = 'PENDENTE')"""
        try:
            rows = self.access.execute_query("SELECT ID_TERMO as id, TERMO_COMPLETO as termo, TIPO_LOCALIZACAO as tipo, STATUS_PROCESSAMENTO as status FROM TB_TERMOS_BUSCA WHERE STATUS_PROCESSAMENTO = 'PENDENTE' ORDER BY ID_TERMO")
            return rows
        except Exception:
            return []

    def approve_change(self, change_id: int, approver: str = 'admin') -> bool:
        """Marca um termo como concluído (aprovação) na TB_TERMOS_BUSCA"""
        conn = self.access._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE TB_TERMOS_BUSCA SET STATUS_PROCESSAMENTO = 'CONCLUIDO', DATA_PROCESSAMENTO = Date() WHERE ID_TERMO = ?", (change_id,))
            conn.commit()
            cursor.close()
            return True
        except Exception:
            try:
                cursor.close()
            except Exception:
                pass
            return False

    def list_paginated_terms(self, limit: int, offset: int) -> List[Dict[str, Any]]:
        """Lista termos de TB_BASE_BUSCA com paginação em Python (fallback para ODBC incompatível).

        Implementação segura: busca todos os termos ativos via `list_active_terms` e realiza
        paginação por slice em memória. Evita queries complexas que Access/ODBC podem não aceitar.
        """
        try:
            try:
                all_rows = self.list_active_terms()
            except Exception:
                all_rows = []

            offset = int(offset) if offset else 0
            limit = int(limit) if limit else 10

            if offset < 0:
                offset = 0
            if limit <= 0:
                limit = 10

            paged = all_rows[offset: offset + limit]
            return paged
        except Exception as e:
            print(f"Erro ao buscar termos paginados (in-memory): {e}")
            return []

    def count_active_terms(self) -> int:
        """Retorna o total de termos ativos em TB_BASE_BUSCA"""
        try:
            rows = self.access.execute_query("SELECT COUNT(*) as cnt FROM TB_BASE_BUSCA WHERE ATIVO = -1")
            if isinstance(rows, list) and rows:
                return int(rows[0].get('cnt', 0) or 0)
            return 0
        except Exception:
            return 0

    def delete_base_term(self, id_base: int) -> bool:
        """Marca termo na TB_BASE_BUSCA como inativo (ATIVO = 0). Se falhar, tenta exclusão física."""
        try:
            conn = self.access._get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE TB_BASE_BUSCA SET ATIVO = 0 WHERE ID_BASE = ?", (id_base,))
                conn.commit()
                cursor.close()
                return True
            except Exception:
                try:
                    cursor.execute("DELETE FROM TB_BASE_BUSCA WHERE ID_BASE = ?", (id_base,))
                    conn.commit()
                    cursor.close()
                    return True
                except Exception:
                    try:
                        cursor.close()
                    except Exception:
                        pass
                    return False
        except Exception:
            return False
