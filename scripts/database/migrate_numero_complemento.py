"""
Script de migração para separar número e complemento em dados existentes
"""
import re
import sys
from pathlib import Path

# Adicionar src ao path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.repositories.access_repository import AccessRepository


def migrate_numero_complemento():
    """Migra dados existentes separando número e complemento"""
    
    print("[MIGRAÇÃO] Iniciando separação de número e complemento...")
    
    try:
        repo = AccessRepository()
        
        # 1. Verificar se coluna COMPLEMENTO existe
        try:
            repo.execute_query("ALTER TABLE TB_ENDERECOS ADD COLUMN COMPLEMENTO TEXT(50)")
            print("[MIGRAÇÃO] ✅ Coluna COMPLEMENTO adicionada")
        except Exception:
            print("[MIGRAÇÃO] ℹ️  Coluna COMPLEMENTO já existe")
        
        # 2. Buscar registros com número para processar
        query = """
        SELECT ID_ENDERECO, NUMERO 
        FROM TB_ENDERECOS 
        WHERE NUMERO IS NOT NULL AND NUMERO <> ''
        """
        
        registros = repo.fetch_all(query)
        
        if not registros:
            print("[MIGRAÇÃO] ℹ️  Nenhum registro para migrar")
            return
            
        print(f"[MIGRAÇÃO] 📋 {len(registros)} registros encontrados para migração")
        
        migrados = 0
        
        for id_endereco, numero_original in registros:
            try:
                # Separar número e complemento
                numero, complemento = parse_numero_complemento(numero_original)
                
                # Atualizar apenas se houve separação
                if complemento:
                    update_query = """
                    UPDATE TB_ENDERECOS 
                    SET NUMERO = ?, COMPLEMENTO = ?
                    WHERE ID_ENDERECO = ?
                    """
                    
                    repo.execute_query(update_query, [numero, complemento, id_endereco])
                    migrados += 1
                    
                    print(f"[MIGRAÇÃO] ✅ ID {id_endereco}: '{numero_original}' → Nº: '{numero}', Compl: '{complemento}'")
                
            except Exception as e:
                print(f"[MIGRAÇÃO] ⚠️  Erro no registro {id_endereco}: {e}")
                continue
        
        print(f"[MIGRAÇÃO] 🎯 Migração concluída: {migrados}/{len(registros)} registros atualizados")
        
        # 3. Verificar resultados
        verificar_migracao(repo)
        
    except Exception as e:
        print(f"[MIGRAÇÃO] ❌ Erro na migração: {e}")


def parse_numero_complemento(numero_completo: str) -> tuple[str, str]:
    """Separa número e complemento usando regex"""
    if not numero_completo:
        return "", ""
        
    numero_completo = numero_completo.strip()
    
    # Padrões para separar número de complemento
    patterns = [
        r'^(\d+)\s+(apto?\.?\s*\d+.*?)$',  # "123 Apto 45", "123 Apt 45"
        r'^(\d+)\s+(sala\s*\d+.*?)$',      # "123 Sala 12"
        r'^(\d+)\s+(bloco?\s*[a-z].*?)$',  # "123 Bloco A"
        r'^(\d+)\s*-\s*([a-zA-Z].*)$',     # "123-A", "123 - Fundos"
        r'^(\d+)\s*([a-zA-Z].+)$',         # "123A", "123 Fundos"
        r'^(\d+)\s+(.+)$',                 # "123 qualquer coisa"
        r'^(\d+)$'                         # Apenas número
    ]
    
    for pattern in patterns:
        match = re.match(pattern, numero_completo, re.IGNORECASE)
        if match:
            if len(match.groups()) == 2:
                numero, complemento = match.groups()
                # Limpar e normalizar complemento
                complemento = re.sub(r'\s+', ' ', complemento.strip())
                return numero.strip(), complemento[:50]  # Limitar a 50 chars
            else:
                return match.group(1).strip(), ""
    
    # Fallback: tudo como número
    return numero_completo, ""


def verificar_migracao(repo):
    """Verifica resultados da migração"""
    try:
        # Contar registros com complemento
        query_complemento = """
        SELECT COUNT(*) FROM TB_ENDERECOS 
        WHERE COMPLEMENTO IS NOT NULL AND COMPLEMENTO <> ''
        """
        
        count_complemento = repo.fetch_one(query_complemento)[0]
        
        # Contar total de endereços
        query_total = "SELECT COUNT(*) FROM TB_ENDERECOS"
        count_total = repo.fetch_one(query_total)[0]
        
        print(f"\n[VERIFICAÇÃO] Resultados da migração:")
        print(f"   Total de endereços: {count_total}")
        print(f"   Com complemento: {count_complemento}")
        print(f"   Percentual: {(count_complemento/count_total*100):.1f}%" if count_total > 0 else "   Percentual: 0%")
        
        # Mostrar alguns exemplos
        query_exemplos = """
        SELECT TOP 5 NUMERO, COMPLEMENTO 
        FROM TB_ENDERECOS 
        WHERE COMPLEMENTO IS NOT NULL AND COMPLEMENTO <> ''
        """
        
        exemplos = repo.fetch_all(query_exemplos)
        
        if exemplos:
            print(f"\n[EXEMPLOS] Registros migrados:")
            for numero, complemento in exemplos:
                print(f"   Número: '{numero}' | Complemento: '{complemento}'")
        
    except Exception as e:
        print(f"[VERIFICAÇÃO] ⚠️  Erro na verificação: {e}")


if __name__ == "__main__":
    migrate_numero_complemento()
    input("\n[INFO] Pressione ENTER para sair...")