"""
Script de migração: adiciona colunas em TB_BASE_BUSCA
Uso: python scripts\database\migrate_search_terms.py
"""
import pyodbc
from pathlib import Path
import sys

PROJECT_ROOT = Path.cwd()
DB_PATH = PROJECT_ROOT / "data" / "pythonsearch.accdb"
CONN_STR = f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={DB_PATH};'

ALTERS = [
    "ALTER TABLE TB_BASE_BUSCA ADD COLUMN IS_TEST BIT",
    "ALTER TABLE TB_BASE_BUSCA ADD COLUMN CREATED_BY TEXT(100)",
    "ALTER TABLE TB_BASE_BUSCA ADD COLUMN UPDATED_BY TEXT(100)",
    "ALTER TABLE TB_BASE_BUSCA ADD COLUMN UPDATED_AT DATE"
]


def run_alters(conn):
    cursor = conn.cursor()
    for sql in ALTERS:
        try:
            cursor.execute(sql)
            print(f"[DB] Executado: {sql}")
        except Exception as e:
            print(f"[DB-AVISO] Não foi possível executar ALTER (provável que já exista): {sql} -> {e}")
    conn.commit()


def seed_base_terms(conn):
    """Insere termos iniciais caso TB_BASE_BUSCA esteja vazia."""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM TB_BASE_BUSCA")
        count = cursor.fetchone()[0]
    except Exception as e:
        print(f"[DB-ERRO] TB_BASE_BUSCA não existe ou não acessível: {e}")
        return

    if count > 0:
        print(f"[DB] TB_BASE_BUSCA já possui {count} registros - pulando seed")
        return

    # Tentar ler constantes do settings (fallback para lista padrão)
    try:
        sys.path.append(str(PROJECT_ROOT / 'src'))
        from config.settings import BASE_BUSCA, BASE_TESTES
        from src.infrastructure.config.config_manager import ConfigManager
        config = ConfigManager()
        base = BASE_TESTES if config.is_test_mode else BASE_BUSCA
        print(f"[DB-DATA] Lendo termos do config (modo teste={config.is_test_mode}) - {len(base)} termos")
    except Exception as e:
        print(f"[DB-AVISO] Não foi possível carregar config/settings: {e}")
        base = [
            "empresa de elevadores", "manutenção de elevadores", "instalação de elevadores",
            "modernização de elevadores", "assistência técnica elevadores", "elevadores residenciais"
        ]
        print(f"[DB-DATA] Usando base padrão com {len(base)} termos")

    cursor = conn.cursor()
    for termo in base:
        try:
            cursor.execute("INSERT INTO TB_BASE_BUSCA (TERMO_BUSCA, CATEGORIA, ATIVO, DATA_CRIACAO) VALUES (?, ?, -1, Date())", (termo, 'base'))
        except Exception as e:
            print(f"[DB-ERRO] Falha ao inserir termo '{termo}': {e}")
    conn.commit()
    print("[DB] Seed de termos inserida")


def main():
    if not DB_PATH.exists():
        print(f"[ERRO] Banco não encontrado em {DB_PATH}. Execute create_db_simple.py primeiro.")
        return

    print(f"[INFO] Conectando em: {DB_PATH}")
    try:
        conn = pyodbc.connect(CONN_STR)
    except Exception as e:
        print(f"[ERRO] Falha ao conectar via pyodbc: {e}")
        return

    run_alters(conn)
    seed_base_terms(conn)

    conn.close()
    print("[OK] Migração finalizada")


if __name__ == '__main__':
    main()
