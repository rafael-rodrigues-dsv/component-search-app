"""
Repository for TB_PLANILHA (spreadsheet)
"""
from src.infrastructure.repositories.access_repository import AccessRepository

class SpreadsheetRepository:
    def __init__(self):
        self._access = AccessRepository()

    def save_to_sheet(self, site_url: str, emails_str: str, telefones_str: str, distancia_km: float = None):
        conn = self._access._get_connection()
        cursor = conn.cursor()
        # Tenta atualizar se já existe
        cursor.execute("SELECT SITE FROM TB_PLANILHA WHERE SITE = ?", (site_url,))
        existing = cursor.fetchone()
        if existing:
            cursor.execute("UPDATE TB_PLANILHA SET EMAIL = ?, TELEFONE = ?, DISTANCIA_KM = ? WHERE SITE = ?", (emails_str, telefones_str, distancia_km, site_url))
        else:
            cursor.execute("INSERT INTO TB_PLANILHA (SITE, EMAIL, TELEFONE, ENDERECO, DISTANCIA_KM) VALUES (?, ?, ?, ?, ?)", (site_url, emails_str, telefones_str, None, distancia_km))
        conn.commit()
        try:
            cursor.close()
        except Exception:
            pass

    def export_to_excel(self, excel_path: str):
        conn = self._access._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT SITE, EMAIL, TELEFONE, ENDERECO, DISTANCIA_KM FROM TB_PLANILHA ORDER BY DISTANCIA_KM, SITE")
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Empresas"
        ws['A1'] = 'SITE'
        ws['B1'] = 'EMAIL'
        ws['C1'] = 'TELEFONE'
        ws['D1'] = 'ENDERECO'
        ws['E1'] = 'DISTANCIA_KM'
        row = 2
        for site, emails, telefones, endereco, distancia in cursor.fetchall():
            ws[f'A{row}'] = site
            ws[f'B{row}'] = emails or ''
            ws[f'C{row}'] = telefones or ''
            ws[f'D{row}'] = endereco or ''
            ws[f'E{row}'] = distancia or ''
            row += 1
        wb.save(excel_path)
        try:
            cursor.close()
        except Exception:
            pass
        return row - 2
