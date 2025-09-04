"""
Repositório para acesso ao banco Access - Substitui JSON
"""
import logging
from pathlib import Path
from typing import List, Dict, Any

import pyodbc


class AccessRepository:
    """Repositório principal para banco Access"""

    def __init__(self):
        self.db_path = Path(__file__).parent.parent.parent.parent / "data" / "pythonsearch.accdb"
        self.conn_str = f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={self.db_path};'
        self.logger = logging.getLogger(__name__)

    def _get_connection(self):
        """Obtém conexão com o banco"""
        return pyodbc.connect(self.conn_str)

    # ===== EMPRESAS =====

    def is_domain_visited(self, domain: str) -> bool:
        """Verifica se domínio já foi visitado (substitui visited.json)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM TB_EMPRESAS WHERE DOMINIO = ?", domain)
            return cursor.fetchone()[0] > 0

    def save_empresa(self, termo_id: int, site_url: str, domain: str, motor_busca: str,
                     endereco: str = None, latitude: float = None, longitude: float = None,
                     distancia_km: float = None) -> int:
        """Salva empresa completa (sempre com estrutura completa)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           INSERT INTO TB_EMPRESAS (ID_TERMO, SITE_URL, DOMINIO, STATUS_COLETA,
                                                    DATA_PRIMEIRA_VISITA, TENTATIVAS_COLETA, MOTOR_BUSCA,
                                                    ENDERECO, LATITUDE, LONGITUDE, DISTANCIA_KM)
                           VALUES (?, ?, ?, 'PENDENTE', Date (), 0, ?, ?, ?, ?, ?)
                           """, termo_id, site_url, domain, motor_busca, endereco, latitude, longitude, distancia_km)
            cursor.execute("SELECT @@IDENTITY")
            empresa_id = cursor.fetchone()[0]
            conn.commit()
            return empresa_id

    def update_empresa_status(self, empresa_id: int, status: str, nome_empresa: str = None):
        """Atualiza status da empresa após coleta"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if nome_empresa:
                cursor.execute("""
                               UPDATE TB_EMPRESAS
                               SET STATUS_COLETA      = ?,
                                   NOME_EMPRESA       = ?,
                                   DATA_ULTIMA_VISITA = Date (), TENTATIVAS_COLETA = TENTATIVAS_COLETA + 1
                               WHERE ID_EMPRESA = ?
                               """, status, nome_empresa, empresa_id)
            else:
                cursor.execute("""
                               UPDATE TB_EMPRESAS
                               SET STATUS_COLETA      = ?,
                                   DATA_ULTIMA_VISITA = Date (), TENTATIVAS_COLETA = TENTATIVAS_COLETA + 1
                               WHERE ID_EMPRESA = ?
                               """, status, empresa_id)
            conn.commit()

    # ===== E-MAILS =====

    def is_email_collected(self, email: str) -> bool:
        """Verifica se e-mail já foi coletado (substitui emails.json)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM TB_EMAILS WHERE EMAIL = ?", email)
            return cursor.fetchone()[0] > 0

    def save_emails(self, empresa_id: int, emails: List[str], domain_email: str):
        """Salva e-mails otimizado"""
        if not emails:
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Inserção em lote
            email_data = [(empresa_id, email, domain_email) for email in emails]
            cursor.executemany("""
                               INSERT INTO TB_EMAILS (ID_EMPRESA, EMAIL, DOMINIO_EMAIL,
                                                      VALIDADO, DATA_COLETA, ORIGEM_COLETA)
                               VALUES (?, ?, ?, -1, Date (), 'SCRAPING')
                               """, email_data)
            conn.commit()

    def save_telefones(self, empresa_id: int, telefones: List[Dict[str, str]]):
        """Salva telefones otimizado"""
        if not telefones:
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Inserção em lote
            phone_data = [(empresa_id, tel['original'], tel['formatted'],
                           tel.get('ddd', ''), tel.get('tipo', 'FIXO')) for tel in telefones]
            cursor.executemany("""
                               INSERT INTO TB_TELEFONES (ID_EMPRESA, TELEFONE, TELEFONE_FORMATADO,
                                                         DDD, TIPO_TELEFONE, VALIDADO, DATA_COLETA)
                               VALUES (?, ?, ?, ?, ?, -1, Date () )
                               """, phone_data)
            conn.commit()

    # ===== TERMOS DE BUSCA =====

    def get_pending_terms(self) -> List[Dict[str, Any]]:
        """Obtém termos pendentes de processamento"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           SELECT ID_TERMO, TERMO_COMPLETO, TIPO_LOCALIZACAO, STATUS_PROCESSAMENTO
                           FROM TB_TERMOS_BUSCA
                           WHERE STATUS_PROCESSAMENTO = 'PENDENTE'
                           ORDER BY ID_TERMO
                           """)
            return [{'id': row[0], 'termo': row[1], 'tipo': row[2], 'status': row[3]}
                    for row in cursor.fetchall()]

    def update_term_status(self, termo_id: int, status: str):
        """Atualiza status do termo"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           UPDATE TB_TERMOS_BUSCA
                           SET STATUS_PROCESSAMENTO = ?,
                               DATA_PROCESSAMENTO   = Date ()
                           WHERE ID_TERMO = ?
                           """, status, termo_id)
            conn.commit()

    def generate_search_terms(self):
        """Gera termos de busca combinando bases + localizações"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Limpar termos existentes
            cursor.execute("DELETE FROM TB_TERMOS_BUSCA")

            # Buscar dados base
            cursor.execute("SELECT ID_BASE, TERMO_BUSCA FROM TB_BASE_BUSCA WHERE ATIVO = -1")
            bases = cursor.fetchall()

            cursor.execute("SELECT ID_ZONA, NOME_ZONA FROM TB_ZONAS WHERE ATIVO = -1")
            zonas = cursor.fetchall()

            cursor.execute("SELECT ID_BAIRRO, NOME_BAIRRO FROM TB_BAIRROS WHERE ATIVO = -1")
            bairros = cursor.fetchall()

            cursor.execute("SELECT ID_CIDADE, NOME_CIDADE FROM TB_CIDADES WHERE ATIVO = -1")
            cidades = cursor.fetchall()

            # Gerar combinações
            for base_id, base_termo in bases:
                # Capital (sem localização específica)
                cursor.execute("""
                               INSERT INTO TB_TERMOS_BUSCA (ID_BASE, TERMO_COMPLETO, TIPO_LOCALIZACAO,
                                                            STATUS_PROCESSAMENTO, DATA_CRIACAO)
                               VALUES (?, ?, 'CAPITAL', 'PENDENTE', Date () )
                               """, base_id, f"{base_termo} São Paulo SP")

                # Zonas
                for zona_id, zona_nome in zonas:
                    cursor.execute("""
                                   INSERT INTO TB_TERMOS_BUSCA (ID_BASE, ID_ZONA, TERMO_COMPLETO,
                                                                TIPO_LOCALIZACAO, STATUS_PROCESSAMENTO, DATA_CRIACAO)
                                   VALUES (?, ?, ?, 'ZONA', 'PENDENTE', Date () )
                                   """, base_id, zona_id, f"{base_termo} {zona_nome} São Paulo SP")

                # Bairros
                for bairro_id, bairro_nome in bairros:
                    cursor.execute("""
                                   INSERT INTO TB_TERMOS_BUSCA (ID_BASE, ID_BAIRRO, TERMO_COMPLETO,
                                                                TIPO_LOCALIZACAO, STATUS_PROCESSAMENTO, DATA_CRIACAO)
                                   VALUES (?, ?, ?, 'BAIRRO', 'PENDENTE', Date () )
                                   """, base_id, bairro_id, f"{base_termo} {bairro_nome} São Paulo SP")

                # Cidades
                for cidade_id, cidade_nome in cidades:
                    cursor.execute("""
                                   INSERT INTO TB_TERMOS_BUSCA (ID_BASE, ID_CIDADE, TERMO_COMPLETO,
                                                                TIPO_LOCALIZACAO, STATUS_PROCESSAMENTO, DATA_CRIACAO)
                                   VALUES (?, ?, ?, 'CIDADE', 'PENDENTE', Date () )
                                   """, base_id, cidade_id, f"{base_termo} {cidade_nome} SP")

            conn.commit()

            # Retornar contagem
            cursor.execute("SELECT COUNT(*) FROM TB_TERMOS_BUSCA")
            return cursor.fetchone()[0]

    # ===== RESET =====

    def reset_collected_data(self):
        """Reset - limpa dados coletados, mantém configurações"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM TB_GEOLOCALIZACAO")
            cursor.execute("DELETE FROM TB_TELEFONES")
            cursor.execute("DELETE FROM TB_EMAILS")
            cursor.execute("DELETE FROM TB_EMPRESAS")
            cursor.execute("UPDATE TB_TERMOS_BUSCA SET STATUS_PROCESSAMENTO = 'PENDENTE', DATA_PROCESSAMENTO = NULL")
            conn.commit()

    # ===== PLANILHA =====

    def save_to_final_sheet(self, site_url: str, emails_str: str, telefones_str: str,
                            endereco: str = None, distancia_km: float = None):
        """Salva/atualiza registro na tabela planilha"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Verificar se já existe
            cursor.execute("SELECT ID_PLANILHA FROM TB_PLANILHA WHERE SITE = ?", site_url)
            existing = cursor.fetchone()

            if existing:
                # Atualizar (preservar distância se não fornecida)
                if distancia_km is not None:
                    cursor.execute("""
                                   UPDATE TB_PLANILHA
                                   SET EMAIL            = ?,
                                       TELEFONE         = ?,
                                       ENDERECO         = ?,
                                       DISTANCIA_KM     = ?,
                                       DATA_ATUALIZACAO = Date ()
                                   WHERE SITE = ?
                                   """, emails_str, telefones_str, endereco, distancia_km, site_url)
                else:
                    cursor.execute("""
                                   UPDATE TB_PLANILHA
                                   SET EMAIL            = ?,
                                       TELEFONE         = ?,
                                       ENDERECO         = ?,
                                       DATA_ATUALIZACAO = Date ()
                                   WHERE SITE = ?
                                   """, emails_str, telefones_str, endereco, site_url)
            else:
                # Inserir novo (sem distância se não fornecida)
                if distancia_km is not None:
                    cursor.execute("""
                                   INSERT INTO TB_PLANILHA (SITE, EMAIL, TELEFONE, ENDERECO, DISTANCIA_KM, DATA_ATUALIZACAO)
                                   VALUES (?, ?, ?, ?, ?, Date () )
                                   """, site_url, emails_str, telefones_str, endereco, distancia_km)
                else:
                    cursor.execute("""
                                   INSERT INTO TB_PLANILHA (SITE, EMAIL, TELEFONE, ENDERECO, DATA_ATUALIZACAO)
                                   VALUES (?, ?, ?, ?, Date () )
                                   """, site_url, emails_str, telefones_str, endereco)

            conn.commit()

    # ===== GEOLOCALIZACAO =====

    def create_geolocation_task(self, empresa_id: int, endereco: str):
        """Cria tarefa de geolocalização para empresa"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           INSERT INTO TB_GEOLOCALIZACAO (ID_EMPRESA, ENDERECO, STATUS_PROCESSAMENTO, TENTATIVAS)
                           VALUES (?, ?, 'PENDENTE', 0)
                           """, empresa_id, endereco)
            conn.commit()

    def get_pending_geolocation_tasks(self) -> List[Dict[str, Any]]:
        """Obtém tarefas de geolocalização pendentes"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           SELECT g.ID_GEO, g.ID_EMPRESA, g.ENDERECO, e.SITE_URL
                           FROM TB_GEOLOCALIZACAO g
                           INNER JOIN TB_EMPRESAS e ON g.ID_EMPRESA = e.ID_EMPRESA
                           WHERE g.STATUS_PROCESSAMENTO = 'PENDENTE'
                           ORDER BY g.ID_GEO
                           """)
            return [{'id_geo': row[0], 'id_empresa': row[1], 'endereco': row[2], 'site_url': row[3]}
                    for row in cursor.fetchall()]

    def update_geolocation_result(self, id_geo: int, latitude: float, longitude: float, distancia_km: float):
        """Atualiza resultado da geolocalização"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Atualizar tabela de controle
            cursor.execute("""
                           UPDATE TB_GEOLOCALIZACAO
                           SET LATITUDE = ?, LONGITUDE = ?, DISTANCIA_KM = ?,
                               STATUS_PROCESSAMENTO = 'CONCLUIDO', DATA_PROCESSAMENTO = Date(),
                               TENTATIVAS = TENTATIVAS + 1
                           WHERE ID_GEO = ?
                           """, latitude, longitude, distancia_km, id_geo)
            
            # Obter ID da empresa
            cursor.execute("SELECT ID_EMPRESA FROM TB_GEOLOCALIZACAO WHERE ID_GEO = ?", id_geo)
            empresa_id = cursor.fetchone()[0]
            
            # Replicar para TB_EMPRESAS
            cursor.execute("""
                           UPDATE TB_EMPRESAS
                           SET LATITUDE = ?, LONGITUDE = ?, DISTANCIA_KM = ?
                           WHERE ID_EMPRESA = ?
                           """, latitude, longitude, distancia_km, empresa_id)
            
            conn.commit()

    def update_geolocation_error(self, id_geo: int, erro_descricao: str):
        """Atualiza erro na geolocalização"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           UPDATE TB_GEOLOCALIZACAO
                           SET STATUS_PROCESSAMENTO = 'ERRO', DATA_PROCESSAMENTO = Date(),
                               TENTATIVAS = TENTATIVAS + 1, ERRO_DESCRICAO = ?
                           WHERE ID_GEO = ?
                           """, erro_descricao, id_geo)
            conn.commit()

    def update_planilha_distance_by_empresa(self, empresa_id: int, distancia_km: float):
        """Atualiza distância na planilha baseado no ID da empresa"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Obter site_url da empresa
            cursor.execute("SELECT SITE_URL FROM TB_EMPRESAS WHERE ID_EMPRESA = ?", empresa_id)
            result = cursor.fetchone()
            if result:
                site_url = result[0]
                cursor.execute("""
                               UPDATE TB_PLANILHA
                               SET DISTANCIA_KM = ?
                               WHERE SITE = ?
                               """, distancia_km, site_url)
                conn.commit()

    def get_geolocation_stats(self) -> Dict[str, int]:
        """Obtém estatísticas de geolocalização"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Total de empresas com endereço
            cursor.execute("SELECT COUNT(*) FROM TB_EMPRESAS WHERE ENDERECO IS NOT NULL AND ENDERECO != ''")
            total_com_endereco = cursor.fetchone()[0]
            
            # Tarefas de geolocalização
            cursor.execute("SELECT COUNT(*) FROM TB_GEOLOCALIZACAO WHERE STATUS_PROCESSAMENTO = 'CONCLUIDO'")
            geocodificadas = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM TB_GEOLOCALIZACAO WHERE STATUS_PROCESSAMENTO = 'PENDENTE'")
            pendentes = cursor.fetchone()[0]
            
            return {
                'total_com_endereco': total_com_endereco,
                'geocodificadas': geocodificadas,
                'pendentes': pendentes,
                'percentual': round((geocodificadas / max(total_com_endereco, 1)) * 100, 1)
            }

    # ===== EXCEL EXPORT =====

    def export_to_excel(self, excel_path: str):
        """Exporta dados para Excel diretamente da tabela planilha"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                           SELECT SITE, EMAIL, TELEFONE, ENDERECO, DISTANCIA_KM
                           FROM TB_PLANILHA
                           ORDER BY DISTANCIA_KM, SITE
                           """)

            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Empresas"

            # Cabeçalho
            ws['A1'] = 'SITE'
            ws['B1'] = 'EMAIL'
            ws['C1'] = 'TELEFONE'
            ws['D1'] = 'ENDERECO'
            ws['E1'] = 'DISTANCIA_KM'

            # Dados
            row = 2
            for site, emails, telefones, endereco, distancia in cursor.fetchall():
                ws[f'A{row}'] = site
                ws[f'B{row}'] = emails or ''
                ws[f'C{row}'] = telefones or ''
                ws[f'D{row}'] = endereco or ''
                ws[f'E{row}'] = distancia or ''
                row += 1

            wb.save(excel_path)
            return row - 2  # Número de registros
