"""
Script para carregar dados iniciais completos no banco Access
"""
import sys
from pathlib import Path

# Adicionar src ao path para imports
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from infrastructure.repositories.access_repository import AccessRepository
from infrastructure.config.config_manager import ConfigManager

sys.path.append(str(Path(__file__).parent.parent.parent))
from config.settings import BASE_ZONAS, BASE_BAIRROS, CIDADES_INTERIOR, BASE_BUSCA, BASE_TESTES


def load_complete_data():
    """Carrega todos os dados do settings.py no banco"""
    repo = AccessRepository()
    config = ConfigManager()

    # Verificar se está em modo teste
    is_test_mode = config.get('mode.is_test', False)
    termos_para_usar = BASE_TESTES if is_test_mode else BASE_BUSCA

    if is_test_mode:
        print("[TESTE] MODO TESTE ATIVADO - Usando termos limitados")
    else:
        print("[PRODUÇÃO] MODO PRODUÇÃO - Usando todos os termos")

    try:
        with repo._get_connection() as conn:
            cursor = conn.cursor()

            print("[INFO] Limpando dados existentes...")
            cursor.execute("DELETE FROM TB_TERMOS_BUSCA")
            cursor.execute("DELETE FROM TB_TELEFONES")
            cursor.execute("DELETE FROM TB_EMAILS")
            cursor.execute("DELETE FROM TB_EMPRESAS")
            cursor.execute("DELETE FROM TB_BASE_BUSCA")
            cursor.execute("DELETE FROM TB_CIDADES")
            cursor.execute("DELETE FROM TB_BAIRROS")
            cursor.execute("DELETE FROM TB_ZONAS")

            print("[INFO] Carregando zonas...")
            for zona in BASE_ZONAS:
                cursor.execute("""
                    INSERT INTO TB_ZONAS (NOME_ZONA, UF, ATIVO, DATA_CRIACAO)
                    VALUES (?, 'SP', -1, Date())
                """, zona)
            print(f"[OK] {len(BASE_ZONAS)} zonas carregadas")

            print("[INFO] Carregando bairros...")
            for bairro in BASE_BAIRROS:
                cursor.execute("""
                    INSERT INTO TB_BAIRROS (NOME_BAIRRO, UF, ATIVO, DATA_CRIACAO)
                    VALUES (?, 'SP', -1, Date())
                """, bairro)
            print(f"[OK] {len(BASE_BAIRROS)} bairros carregados")

            print("[INFO] Carregando cidades...")
            for cidade in CIDADES_INTERIOR:
                cursor.execute("""
                    INSERT INTO TB_CIDADES (NOME_CIDADE, UF, ATIVO, DATA_CRIACAO)
                    VALUES (?, 'SP', -1, Date())
                """, cidade)
            print(f"[OK] {len(CIDADES_INTERIOR)} cidades carregadas")

            print("[INFO] Carregando termos base...")
            for termo in termos_para_usar:
                cursor.execute("""
                    INSERT INTO TB_BASE_BUSCA (TERMO_BUSCA, CATEGORIA, ATIVO, DATA_CRIACAO)
                    VALUES (?, 'elevadores', -1, Date())
                """, termo)
            print(f"[OK] {len(termos_para_usar)} termos base carregados")

            conn.commit()

            print("\n[INFO] Gerando termos de busca...")
            count = repo.generate_search_terms()
            print(f"[OK] {count} termos de busca gerados")

            print("\n[SUCESSO] DADOS INICIAIS CARREGADOS COM SUCESSO!")
            print(
                f"[INFO] Total: {len(BASE_ZONAS)} zonas + {len(BASE_BAIRROS)} bairros + {len(CIDADES_INTERIOR)} cidades + {len(termos_para_usar)} termos = {count} combinações")

    except Exception as e:
        print(f"[ERRO] {e}")


if __name__ == "__main__":
    load_complete_data()
    input("Pressione ENTER para sair...")
