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

        # Garantir que o CEP de referência esteja presente em TB_CEP_CONFIG antes de gerar termos
        try:
            from src.application.services.zip_code_service import ZipCodeService
            from src.infrastructure.config.config_manager import ConfigManager
            zip_svc = ZipCodeService()
            # Use ConfigManager.reference_cep (preferirá valor do DB quando disponível)
            cfg = ConfigManager()
            yaml_cep = cfg.reference_cep
            # Se não houver registro no DB, tentar gravar usando o CEP do YAML
            try:
                existing = zip_svc.get_reference_cep()
                if not existing and yaml_cep:
                    print(f"[INFO] Inserindo CEP de referência a partir do YAML: {yaml_cep}")
                    ok = zip_svc.set_reference_cep(yaml_cep)
                    if ok:
                        print("[OK] TB_CEP_CONFIG inicializada com sucesso")
                    else:
                        print("[AVISO] Falha ao inicializar TB_CEP_CONFIG a partir do YAML")
            except Exception as e:
                print(f"[AVISO] Erro ao verificar/seed TB_CEP_CONFIG: {e}")
        except Exception:
            # Se ZipCodeService não estiver disponível, seguimos com a inicialização normal
            pass

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