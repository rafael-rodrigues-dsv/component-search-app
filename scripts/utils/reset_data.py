"""
Script utilitário para reset dos dados coletados
"""
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from application.services.database_service import DatabaseService

def reset_collected_data():
    """Reset dos dados coletados, mantendo configurações"""
    try:
        db_service = DatabaseService()
        
        print("⚠️  RESET DOS DADOS COLETADOS")
        print("=" * 40)
        print("Isso irá limpar:")
        print("- Empresas encontradas")
        print("- E-mails coletados") 
        print("- Telefones coletados")
        print("- Status dos termos (volta para PENDENTE)")
        print()
        print("Será mantido:")
        print("- Zonas, bairros, cidades")
        print("- Termos base de busca")
        print("- Estrutura do banco")
        print()
        
        confirm = input("Confirma o reset? (s/N): ")
        
        if confirm.lower() == 's':
            print("\n🔄 Executando reset...")
            db_service.reset_data(confirm=True)
            print("✅ Reset concluído!")
        else:
            print("❌ Reset cancelado")
            
    except Exception as e:
        print(f"❌ ERRO: {e}")

if __name__ == "__main__":
    reset_collected_data()
    input("⏸️ ENTER para sair...")