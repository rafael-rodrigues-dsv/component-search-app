"""
Repository for TB_ENDERECOS
"""
from typing import Optional, List, Tuple
from src.infrastructure.repositories.access_repository import AccessRepository

class AddressesRepository:
    def __init__(self):
        self._access = AccessRepository()

    def insert_address(self, address_model) -> Optional[int]:
        """Insere endereço estruturado e retorna ID (implementação simplificada/portada)."""
        if not address_model:
            return None

        try:
            conn = self._access._get_connection()
            cursor = conn.cursor()
            # Verificar se tabela existe
            try:
                cursor.execute("SELECT COUNT(*) FROM TB_ENDERECOS")
            except Exception:
                try:
                    cursor.close()
                except Exception:
                    pass
                return None

            cursor.execute(
                "SELECT ID_ENDERECO FROM TB_ENDERECOS WHERE LOGRADOURO = ? AND NUMERO = ? AND COMPLEMENTO = ? AND BAIRRO = ?",
                (address_model.logradouro, address_model.numero, address_model.complemento, address_model.bairro)
            )
            existing = cursor.fetchone()
            if existing:
                try:
                    cursor.close()
                except Exception:
                    pass
                return existing[0]

            cursor.execute(
                """
                INSERT INTO TB_ENDERECOS (LOGRADOURO, NUMERO, COMPLEMENTO, BAIRRO, CIDADE, ESTADO, CEP, DATA_CRIACAO)
                VALUES (?, ?, ?, ?, ?, ?, ?, Date())
                """,
                (address_model.logradouro, address_model.numero, address_model.complemento, address_model.bairro,
                 address_model.cidade, address_model.estado, address_model.cep)
            )
            cursor.execute("SELECT @@IDENTITY")
            endereco_id = cursor.fetchone()[0]
            conn.commit()
            try:
                cursor.close()
            except Exception:
                pass
            return endereco_id
        except Exception:
            return None

    def update_corrected(self, endereco_id: int, corrected_address) -> None:
        try:
            conn = self._access._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE TB_ENDERECOS 
                SET LOGRADOURO = ?, NUMERO = ?, COMPLEMENTO = ?, BAIRRO = ?, CIDADE = ?, ESTADO = ?
                WHERE ID_ENDERECO = ?
                """,
                (
                    corrected_address.logradouro,
                    corrected_address.numero,
                    corrected_address.complemento,
                    corrected_address.bairro,
                    corrected_address.cidade,
                    corrected_address.estado,
                    endereco_id
                )
            )
            conn.commit()
            try:
                cursor.close()
            except Exception:
                pass
        except Exception:
            pass

    def fetch_with_cep_for_enrichment(self) -> List[Tuple[int, str, str]]:
        """Busca endereços com CEP que ainda não foram geocodificados (formato: (empresa_id, endereco_str, cep))."""
        conn = self._access._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT e.ID_EMPRESA, en.LOGRADOURO, en.NUMERO, en.BAIRRO, en.CIDADE, en.CEP
            FROM TB_EMPRESAS e
            INNER JOIN TB_ENDERECOS en ON e.ID_ENDERECO = en.ID_ENDERECO
            WHERE en.CEP IS NOT NULL 
            AND en.CEP <> ''
            AND (e.LATITUDE IS NULL OR e.LONGITUDE IS NULL)
            """
        )
        results = cursor.fetchall()
        formatted = []
        for row in results:
            empresa_id, logr, num, bairro, cidade, cep = row
            parts = []
            if logr: parts.append(logr)
            if num: parts.append(num)
            if bairro: parts.append(bairro)
            if cidade: parts.append(cidade)
            endereco_concat = ', '.join(parts) if parts else ''
            if cep:
                formatted.append((empresa_id, endereco_concat, cep))
        try:
            cursor.close()
        except Exception:
            pass
        return formatted

    def update_enriched_for_empresa(self, empresa_id: int, enriched_address) -> None:
        """Atualiza endereço associado a uma empresa (helper)"""
        try:
            conn = self._access._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ID_ENDERECO FROM TB_EMPRESAS WHERE ID_EMPRESA = ?", (empresa_id,))
            res = cursor.fetchone()
            if not res:
                try:
                    cursor.close()
                except Exception:
                    pass
                return
            endereco_id = res[0]
            try:
                cursor.close()
            except Exception:
                pass
            return self.update_corrected(endereco_id, enriched_address)
        except Exception:
            return None
