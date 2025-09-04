"""Script para inicializar dados básicos no banco Access"""
import sys
from pathlib import Path

# Adicionar src ao path para imports
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from infrastructure.repositories.access_repository import AccessRepository


def initialize_database():
    """Inicializa o banco com dados básicos"""
    repo = AccessRepository()
    
    try:
        print("[INFO] Inicializando banco de dados...")
        
        # Gerar termos de busca se necessário
        count = repo.generate_search_terms()
        
        if count > 0:
            print(f"[OK] {count} termos de busca inicializados")
        else:
            print("[INFO] Termos já existem no banco")
            
        print("\n[OK] Banco inicializado com sucesso!")
        
    except Exception as e:
        print(f"[ERRO] Falha na inicialização: {e}")


if __name__ == "__main__":
    initialize_database()
    input("Pressione ENTER para sair...")