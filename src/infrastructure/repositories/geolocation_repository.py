"""
Repository for TB_GEOLOCALIZACAO
"""
from typing import List, Dict
from src.infrastructure.repositories.access_repository import AccessRepository

class GeolocationRepository:
    def __init__(self):
        self._access = AccessRepository()

    def create_task(self, empresa_id: int, endereco_id: int):
        if not endereco_id:
            return
        conn = self._access._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ID_GEO FROM TB_GEOLOCALIZACAO WHERE ID_ENDERECO = ?", (endereco_id,))
        existing = cursor.fetchone()
        if not existing:
            cursor.execute(
                "INSERT INTO TB_GEOLOCALIZACAO (ID_EMPRESA, ID_ENDERECO, STATUS_PROCESSAMENTO, TENTATIVAS) VALUES (?, ?, 'PENDENTE', 0)",
                (empresa_id, endereco_id)
            )
            conn.commit()
        try:
            cursor.close()
        except Exception:
            pass

    def fetch_pending(self) -> List[Dict]:
        conn = self._access._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT g.ID_GEO, g.ID_EMPRESA, g.ID_ENDERECO, emp.SITE_URL,
                   end.LOGRADOURO, end.NUMERO, end.COMPLEMENTO, end.BAIRRO, end.CIDADE, end.ESTADO, end.CEP
            FROM (TB_GEOLOCALIZACAO g 
            INNER JOIN TB_EMPRESAS emp ON g.ID_EMPRESA = emp.ID_EMPRESA)
            INNER JOIN TB_ENDERECOS end ON g.ID_ENDERECO = end.ID_ENDERECO
            WHERE g.STATUS_PROCESSAMENTO = 'PENDENTE'
            ORDER BY g.ID_GEO
            """
        )
        tasks = []
        for row in cursor.fetchall():
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
                'id_geo': row[0],
                'id_empresa': row[1],
                'id_endereco': row[2],
                'site_url': row[3],
                'address_model': address
            })
        try:
            cursor.close()
        except Exception:
            pass
        return tasks

    def update_success(self, id_geo: int, latitude: float, longitude: float, distancia_km: float):
        conn = self._access._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE TB_GEOLOCALIZACAO
            SET LATITUDE = ?, LONGITUDE = ?, DISTANCIA_KM = ?,
                STATUS_PROCESSAMENTO = 'CONCLUIDO', DATA_PROCESSAMENTO = Date(),
                TENTATIVAS = TENTATIVAS + 1
            WHERE ID_GEO = ?
            """,
            (latitude, longitude, distancia_km, id_geo)
        )
        # Replicar coordenadas para empresa e planilha
        cursor.execute("SELECT ID_EMPRESA FROM TB_GEOLOCALIZACAO WHERE ID_GEO = ?", (id_geo,))
        empresa_id = cursor.fetchone()[0]
        cursor.execute("UPDATE TB_EMPRESAS SET LATITUDE = ?, LONGITUDE = ?, DISTANCIA_KM = ? WHERE ID_EMPRESA = ?", (latitude, longitude, distancia_km, empresa_id))
        cursor.execute("SELECT SITE_URL FROM TB_EMPRESAS WHERE ID_EMPRESA = ?", (empresa_id,))
        site_result = cursor.fetchone()
        if site_result:
            site_url = site_result[0]
            cursor.execute("UPDATE TB_PLANILHA SET DISTANCIA_KM = ? WHERE SITE = ?", (distancia_km, site_url))
        conn.commit()
        try:
            cursor.close()
        except Exception:
            pass

    def update_error(self, id_geo: int, erro_descricao: str):
        conn = self._access._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE TB_GEOLOCALIZACAO
            SET STATUS_PROCESSAMENTO = 'ERRO', DATA_PROCESSAMENTO = Date(),
                TENTATIVAS = TENTATIVAS + 1, ERRO_DESCRICAO = ?
            WHERE ID_GEO = ?
            """,
            (erro_descricao, id_geo)
        )
        conn.commit()
        try:
            cursor.close()
        except Exception:
            pass

    def get_stats(self) -> Dict[str, int]:
        try:
            conn = self._access._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM TB_EMPRESAS WHERE ID_ENDERECO IS NOT NULL")
            total_com_endereco = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM TB_GEOLOCALIZACAO WHERE STATUS_PROCESSAMENTO = 'CONCLUIDO'")
            geocodificadas = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM TB_GEOLOCALIZACAO WHERE STATUS_PROCESSAMENTO = 'PENDENTE'")
            pendentes = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM TB_GEOLOCALIZACAO WHERE STATUS_PROCESSAMENTO = 'ERRO'")
            erros = cursor.fetchone()[0]
            try:
                cursor.close()
            except Exception:
                pass
            return {
                'total_com_endereco': total_com_endereco,
                'geocodificadas': geocodificadas,
                'pendentes': pendentes,
                'erros': erros,
                'percentual': round((geocodificadas / max(total_com_endereco, 1)) * 100, 1)
            }
        except Exception as e:
            return {'total_com_endereco': 0, 'geocodificadas': 0, 'pendentes': 0, 'erros': 0, 'percentual': 0}
