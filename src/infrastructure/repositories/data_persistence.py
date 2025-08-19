"""
Camada de Infraestrutura - Persistência de dados
"""
import json
import os
from typing import Dict, List, Set
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment

from ...domain.email_processor import Company


class JsonRepository:
    """Repositório JSON para controle de visitados e e-mails"""
    
    def __init__(self, visited_path: str, emails_path: str):
        self.visited_path = visited_path
        self.emails_path = emails_path
    
    def load_visited_domains(self) -> Dict[str, bool]:
        """Carrega domínios já visitados"""
        return self._load_json(self.visited_path) or {}
    
    def save_visited_domains(self, visited: Dict[str, bool]):
        """Salva domínios visitados"""
        self._save_json(self.visited_path, visited)
    
    def load_seen_emails(self) -> Set[str]:
        """Carrega e-mails já coletados"""
        emails_list = self._load_json(self.emails_path) or []
        return set(emails_list)
    
    def save_seen_emails(self, emails: Set[str]):
        """Salva e-mails coletados"""
        self._save_json(self.emails_path, list(emails))
    
    def _load_json(self, path: str):
        """Carrega arquivo JSON"""
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return None
        return None
    
    def _save_json(self, path: str, data):
        """Salva arquivo JSON"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class ExcelRepository:
    """Repositório Excel para empresas"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._ensure_excel_exists()
    
    def save_company(self, company: Company):
        """Salva empresa no Excel"""
        if not company.emails:
            return
        
        try:
            wb = load_workbook(self.file_path)
            ws = wb["Dados"]
            
            emails_str = ";".join(company.emails)
            ws.append([company.name, emails_str, company.search_term, company.address])
            
            # Formatação da linha
            for i, cell in enumerate(ws[ws.max_row]):
                if i == 0:  # Nome da empresa
                    cell.font = Font(name="Arial", size=10, bold=True)
                else:
                    cell.font = Font(name="Arial", size=10)
                cell.alignment = Alignment(horizontal="left")
            
            wb.save(self.file_path)
            
        except Exception:
            pass
    
    def _ensure_excel_exists(self):
        """Garante que arquivo Excel existe"""
        if not os.path.exists(self.file_path):
            wb = Workbook()
            ws = wb.active
            ws.title = "Dados"
            ws["A1"] = "NOME"
            ws["B1"] = "EMAIL"
            ws["C1"] = "TERMO BUSCA"
            ws["D1"] = "ENDEREÇO"
            
            # Ajusta largura das colunas
            ws.column_dimensions['A'].width = 30
            ws.column_dimensions['B'].width = 35
            ws.column_dimensions['C'].width = 40
            ws.column_dimensions['D'].width = 50
            
            # Formatação do cabeçalho
            for cell in ws[1]:
                cell.font = Font(name="Arial", size=10, bold=True)
                cell.alignment = Alignment(horizontal="left")
            
            wb.save(self.file_path)