#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python Search App - Coletor de E-mails e Contatos
Ponto de entrada principal da aplicação
"""
import sys
import webbrowser
from pathlib import Path

from src.__version__ import __version__
from src.application.services.database_application_service import DatabaseApplicationService
from src.web.dashboard_server import start_dashboard, stop_dashboard


def _create_database_automatically() -> bool:
    """Cria o banco Access automaticamente"""
    try:
        from scripts.database.create_db_simple import create_simple_db
        
        # Executar criação diretamente
        create_simple_db(auto_mode=True)
        
        # Verificar se banco foi criado
        db_path = Path("data/pythonsearch.accdb")
        return db_path.exists()
            
    except Exception as e:
        print(f"[ERRO] Falha na criação: {e}")
        return False


def _create_cache_automatically() -> bool:
    """Cria o banco de cache SQLite automaticamente"""
    try:
        cache_path = Path("data/cache/cache.db")

        # Se já existe, não precisa criar
        if cache_path.exists():
            return True

        print("[INFO] Cache SQLite não encontrado. Criando automaticamente...")

        from scripts.database.create_cache_db import create_cache_db

        # Criar diretório se não existir
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        # Executar criação do cache (sem interação)
        # Importar função e executar diretamente
        import sqlite3
        conn = sqlite3.connect(cache_path)

        # Criar tabelas
        tables_sql = [
            """CREATE TABLE IF NOT EXISTS cep_cache (
                cep TEXT PRIMARY KEY,
                cidade TEXT,
                uf TEXT,
                bairro TEXT,
                logradouro TEXT,
                complemento TEXT,
                source TEXT,
                timestamp INTEGER,
                hit_count INTEGER DEFAULT 1
            )""",
            """CREATE TABLE IF NOT EXISTS geocoding_cache (
                address_hash TEXT PRIMARY KEY,
                address TEXT,
                latitude REAL,
                longitude REAL,
                source TEXT,
                timestamp INTEGER,
                hit_count INTEGER DEFAULT 1
            )""",
            """CREATE TABLE IF NOT EXISTS distance_cache (
                origin_lat REAL,
                origin_lon REAL,
                dest_lat REAL,
                dest_lon REAL,
                distance_km REAL,
                timestamp INTEGER,
                hit_count INTEGER DEFAULT 1,
                PRIMARY KEY (origin_lat, origin_lon, dest_lat, dest_lon)
            )""",
            """CREATE TABLE IF NOT EXISTS cities (
                id TEXT PRIMARY KEY,
                name TEXT,
                state TEXT,
                population INTEGER,
                is_capital BOOLEAN,
                region_type TEXT,
                latitude REAL,
                longitude REAL
            )"""
        ]

        # Criar índices
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_cep_uf ON cep_cache(uf)",
            "CREATE INDEX IF NOT EXISTS idx_cep_timestamp ON cep_cache(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_geocoding_timestamp ON geocoding_cache(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_distance_origin ON distance_cache(origin_lat, origin_lon)",
            "CREATE INDEX IF NOT EXISTS idx_distance_timestamp ON distance_cache(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_cities_state ON cities(state)",
            "CREATE INDEX IF NOT EXISTS idx_cities_population ON cities(population DESC)",
            "CREATE INDEX IF NOT EXISTS idx_cities_coords ON cities(latitude, longitude)",
            "CREATE INDEX IF NOT EXISTS idx_cities_search ON cities(name, state)"
        ]

        # Executar SQLs
        for sql in tables_sql:
            conn.execute(sql)

        for sql in indexes_sql:
            conn.execute(sql)

        conn.commit()
        conn.close()

        print("[OK] Cache SQLite criado com sucesso!")
        return cache_path.exists()

    except Exception as e:
        print(f"[ERRO] Falha ao criar cache: {e}")
        return False



def main():
    """Função principal da aplicação"""
    from src.infrastructure.config.config_manager import ConfigManager
    config = ConfigManager()

    # --- Verificação/autoupdate do ChromeDriver antes de iniciar a aplicação ---
    try:
        from src.infrastructure.drivers.chromedriver_updater import update_chromedriver
        print('[INFO] Verificando ChromeDriver antes de iniciar a aplicação...')
        try:
            updated = update_chromedriver('drivers/chromedriver.exe')
            if updated:
                print('[OK] ChromeDriver verificado/atualizado com sucesso')
            else:
                print('[AVISO] Não foi possível garantir atualização automática do ChromeDriver; continuará com o driver atual (se houver)')
        except Exception as e:
            print(f'[AVISO] Erro ao executar updater do ChromeDriver: {e}')
    except Exception:
        # helper indisponível — continuar normalmente
        print('[AVISO] Módulo de atualização do ChromeDriver não disponível; pulando verificação automática')

    # Mostrar modo de operação
    mode_text = "TESTE" if config.is_test_mode else "PRODUÇÃO"
    print(f"[INFO] Iniciando Python Search App - Coletor de E-mails e Contatos v{__version__}")
    print(f"[INFO] Modo de operação: {mode_text}")

    # Verificar se banco Access existe (cria automaticamente se necessário)
    db_path = Path("data/pythonsearch.accdb")

    if not db_path.exists():
        print("[INFO] Banco Access não encontrado. Criando automaticamente...")
        if not _create_database_automatically():
            print("[ERRO] Falha ao criar banco de dados")
            return 1
        print("[OK] Banco criado com sucesso!")
        # Pequeno atraso para garantir que o Access COM liberou o arquivo
        try:
            import time
            time.sleep(0.5)
        except Exception:
            pass

    # Verificar se cache SQLite existe (cria automaticamente se necessário)
    cache_path = Path("data/cache/cache.db")
    if not cache_path.exists():
        if not _create_cache_automatically():
            print("[AVISO] Falha ao criar cache SQLite - sistema continuará sem cache")
        # Cache não é crítico, então não retorna erro

    # Inicializar banco de dados
    print("[INFO] Inicializando banco de dados...")
    print("[INFO] Conectando ao banco Access...")
    
    try:
        # Antes de inicializar o singleton, aguardar até que ODBC consiga abrir conexão (evita race com Access COM)
        from src.infrastructure.logging.initial_load_logger import load_logger
        from src.infrastructure.repositories.access_repository import AccessRepository

        max_wait_sec = 15
        waited = 0
        wait_step = 0.5
        last_exc = None
        while waited <= max_wait_sec:
            try:
                # Tenta criar o singleton e obter conexão
                repo = AccessRepository()
                conn = repo._get_connection()
                # Se conseguiu, sair do loop
                load_logger.debug(f"ODBC conectado ao banco após {waited:.1f}s")
                break
            except Exception as e:
                last_exc = e
                load_logger.debug(f"Aguardando liberação do arquivo .accdb (esperado pela criação)... tentativa mun {waited:.1f}s: {e}")
                import time
                time.sleep(wait_step)
                waited += wait_step
                continue
        else:
            # Exauriu tempo
            load_logger.error(f"Timeout aguardando liberação do arquivo .accdb: {last_exc}")
            raise last_exc

        db_service = DatabaseApplicationService()
        print("[OK] Conexão singleton estabelecida com sucesso")

        # Garantir que a tabela TB_CEP_CONFIG exista e esteja populada ANTES da descoberta dinâmica
        try:
            from src.application.services.zip_code_application_service import ZipCodeApplicationService
            zip_svc = ZipCodeApplicationService()
            seeded = zip_svc.ensure_table_and_seed()
            if seeded:
                print('[INFO] TB_CEP_CONFIG garantida e seed aplicada (se necessário) via ZipCodeService')
            else:
                print('[AVISO] Não foi possível garantir TB_CEP_CONFIG via ZipCodeService')
        except Exception as e:
            print(f"[AVISO] Erro verificando/seed TB_CEP_CONFIG via service: {e}")

    except Exception as e:
        print(f"[ERRO] Falha ao conectar com banco: {e}")
        print("[INFO] Tentando recriar banco...")

    # Iniciar dashboard web (interface principal de execução)
    print("\n=== PYTHON SEARCH APP ===")
    print("[INFO] Iniciando dashboard web (interface principal). Use a UI para controlar fluxos e configurar termos.")
    dashboard = None
    try:
        dashboard = start_dashboard()
        if dashboard and config.get_config_value('dashboard.auto_open_browser', True):
            try:
                webbrowser.open('http://127.0.0.1:5000')
                print("[OK] Dashboard aberto no navegador")
            except Exception:
                print("[AVISO] Não foi possível abrir o navegador automaticamente. Acesse: http://127.0.0.1:5000")
    except Exception as e:
        print(f"[AVISO] Dashboard web não disponível: {e}")

    # Bloquear o processo principal mantendo o dashboard rodando (aguardar Ctrl+C)
    try:
        print('[INFO] Pressione Ctrl+C para encerrar o servidor e sair')
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print('\n[INFO] Encerrando...')
    finally:
        try:
            stop_dashboard()
        except:
            pass
        try:
            from src.infrastructure.repositories.access_repository import AccessRepository
            AccessRepository().close_connection()
        except:
            pass
        return 0



if __name__ == "__main__":
    sys.exit(main())