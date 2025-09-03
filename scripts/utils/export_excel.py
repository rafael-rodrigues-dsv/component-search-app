"""
Script utilitário para exportar dados do Access para Excel
"""
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from application.services.database_service import DatabaseService

def export_to_excel():
    """Exporta dados do banco para Excel"""
    try:
        db_service = DatabaseService()
        
        print("📊 Exportando dados para Excel...")
        success, count = db_service.export_to_excel()
        
        if success:
            print(f"✅ Excel gerado com {count} registros")
            print("📍 Local: output/empresas.xlsx")
        else:
            print("❌ Falha na exportação")
            
    except Exception as e:
        print(f"❌ ERRO: {e}")

if __name__ == "__main__":
    export_to_excel()
    input("⏸️ ENTER para sair...")