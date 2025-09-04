"""
Script utilitário para exportar dados do Access para Excel
"""
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from application.services.excel_application_service import ExcelApplicationService


def export_to_excel():
    """Exporta dados do banco para Excel"""
    try:
        excel_service = ExcelApplicationService()

        print("📊 Exportando dados para Excel...")
        result = excel_service.export_excel()

        if result['success']:
            print(f"✅ {result['message']}")
            print(f"📍 Local: {result['path']}")
        else:
            print(f"❌ {result['message']}")

    except Exception as e:
        print(f"❌ ERRO: {e}")


if __name__ == "__main__":
    export_to_excel()
    input("⏸️ ENTER para sair...")
