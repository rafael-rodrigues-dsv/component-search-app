from src.infrastructure.repositories.spreadsheet_repository import SpreadsheetRepository

class SpreadsheetApplicationService:
    def __init__(self):
        self.repo = SpreadsheetRepository()

    def save(self, site_url: str, emails_str: str, telefones_str: str, distancia_km: float = None):
        return self.repo.save_to_sheet(site_url, emails_str, telefones_str, distancia_km)

    def export(self, path: str):
        return self.repo.export_excel(path)
