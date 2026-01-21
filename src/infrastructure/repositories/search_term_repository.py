"""
Repositório para gerenciamento de termos de busca (TB_BASE_BUSCA)
"""
from typing import List, Dict, Any
from .access_repository import AccessRepository


class SearchTermRepository:
    def __init__(self):
        self.access = AccessRepository()

    def list_active_terms(self, is_test: bool = False) -> List[Dict[str, Any]]:
        """Retorna termos ativos (ATIVO = -1) da TB_BASE_BUSCA"""
        try:
            # Retornar termos ativos da base, independente do campo IS_TEST.
            query = "SELECT ID_BASE, TERMO_BUSCA, CATEGORIA, ATIVO, DATA_CRIACAO FROM TB_BASE_BUSCA WHERE ATIVO = -1"
            return self.access.execute_query(query)
        except Exception:
            return []

    def insert_term(self, termo: str, categoria: str = 'base', is_test: bool = False) -> int:
        conn = self.access._get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO TB_BASE_BUSCA (TERMO_BUSCA, CATEGORIA, ATIVO, DATA_CRIACAO, IS_TEST) VALUES (?, ?, -1, Date(), ?)", (termo, categoria, -1 if is_test else 0))
        cursor.execute("SELECT @@IDENTITY")
        id_base = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        return id_base

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
        """Lista termos de TB_BASE_BUSCA com paginação, compatível com Microsoft Access."""
        try:
            # Garantir inteiros
            offset = int(offset) if offset else 0
            limit = int(limit) if limit else 10

            # Caso simples (primeira página) - evitar subqueries desnecessárias
            if offset == 0:
                paginated_query = f"SELECT TOP {limit} * FROM TB_BASE_BUSCA WHERE ATIVO = -1 ORDER BY ID_BASE"
            else:
                # Padrão compatível com Access usando TOP + subquery (inner ordenado desc)
                total_top = offset + limit
                paginated_query = f"""
                    SELECT * FROM (
                        SELECT TOP {limit} * FROM (
                            SELECT TOP {total_top} * FROM TB_BASE_BUSCA WHERE ATIVO = -1 ORDER BY ID_BASE DESC
                        ) AS innerq
                        ORDER BY ID_BASE
                    ) AS outerq
                    ORDER BY ID_BASE
                """

            return self.access.execute_query(paginated_query)
        except Exception as e:
            print(f"Erro ao buscar termos paginados: {e}")
            return []

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
