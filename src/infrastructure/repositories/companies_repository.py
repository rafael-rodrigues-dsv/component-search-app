"""
Repository for TB_EMPRESAS with real implementations (moved from AccessRepository)
"""
from typing import Optional, Dict
from src.infrastructure.repositories.access_repository import AccessRepository

class CompaniesRepository:
    def __init__(self):
        self._access = AccessRepository()

    def insert_company(self, termo_id: int, site_url: str, domain: str, motor_busca: str, address_model=None, latitude=None, longitude=None, distancia_km=None) -> Optional[int]:
        """Insere empresa e retorna ID (implementação extraída de AccessRepository.save_empresa)"""
        conn = self._access._get_connection()
        cursor = conn.cursor()

        # Salvar endereço se houver (addresses repo deve ser usado pelo chamador quando apropriado)
        endereco_id = None
        if address_model:
            # try using AddressesRepository if available to avoid duplication
            try:
                from src.infrastructure.repositories.addresses_repository import AddressesRepository
                addr_repo = AddressesRepository()
                endereco_id = addr_repo.insert_address(address_model)
            except Exception:
                endereco_id = None

        cursor.execute(
            """
            INSERT INTO TB_EMPRESAS (ID_TERMO, SITE_URL, DOMINIO, STATUS_COLETA,
                                     DATA_PRIMEIRA_VISITA, TENTATIVAS_COLETA, MOTOR_BUSCA,
                                     ID_ENDERECO, LATITUDE, LONGITUDE, DISTANCIA_KM)
            VALUES (?, ?, ?, ?, Date (), ?, ?, ?, ?, ?, ?)
            """,
            (termo_id, site_url, domain, 'PENDENTE', 0, motor_busca, endereco_id, latitude, longitude, distancia_km)
        )
        cursor.execute("SELECT @@IDENTITY")
        empresa_id = cursor.fetchone()[0]
        conn.commit()
        try:
            cursor.close()
        except Exception:
            pass
        return empresa_id

    def update_status(self, empresa_id: int, status: str, nome_empresa: str = None):
        """Atualiza status da empresa"""
        conn = self._access._get_connection()
        cursor = conn.cursor()
        if nome_empresa:
            cursor.execute(
                """
                UPDATE TB_EMPRESAS
                SET STATUS_COLETA      = ?,
                    NOME_EMPRESA       = ?,
                    DATA_ULTIMA_VISITA = Date (), TENTATIVAS_COLETA = TENTATIVAS_COLETA + 1
                WHERE ID_EMPRESA = ?
                """,
                (status, nome_empresa, empresa_id)
            )
        else:
            cursor.execute(
                """
                UPDATE TB_EMPRESAS
                SET STATUS_COLETA      = ?,
                    DATA_ULTIMA_VISITA = Date (), TENTATIVAS_COLETA = TENTATIVAS_COLETA + 1
                WHERE ID_EMPRESA = ?
                """,
                (status, empresa_id)
            )
        conn.commit()
        try:
            cursor.close()
        except Exception:
            pass

    def is_domain_visited(self, domain: str) -> bool:
        """Verifica se domínio já foi visitado"""
        try:
            conn = self._access._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM TB_EMPRESAS WHERE DOMINIO = ?", (domain,))
            result = cursor.fetchone()
            try:
                cursor.close()
            except Exception:
                pass
            return result[0] > 0
        except Exception:
            return False

    def get_collection_statistics(self) -> Dict[str, int]:
        """Retorna estatísticas de coleta de empresas (visitadas/coletadas/nao_coletadas)"""
        try:
            conn = self._access._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM TB_EMPRESAS")
            visitadas = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM TB_EMPRESAS WHERE STATUS_COLETA = 'COLETADO'")
            coletadas = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM TB_EMPRESAS WHERE STATUS_COLETA = 'NAO_COLETADO'")
            nao_coletadas = cursor.fetchone()[0]
            try:
                cursor.close()
            except Exception:
                pass
            taxa = round((coletadas / max(visitadas, 1)) * 100, 1) if visitadas > 0 else 0
            return {'visitadas': visitadas, 'coletadas': coletadas, 'nao_coletadas': nao_coletadas, 'taxa_coleta_pct': taxa}
        except Exception:
            return {'visitadas': 0, 'coletadas': 0, 'nao_coletadas': 0, 'taxa_coleta_pct': 0}
