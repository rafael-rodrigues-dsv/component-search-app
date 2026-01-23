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


def _check_browser_availability(browser: str) -> bool:
    """Verifica se o navegador está disponível (verificação rápida de arquivo)"""
    import os

    if browser == "CHROME":
        return os.path.exists(r"C:\Program Files\Google\Chrome\Application\chrome.exe") or \
            os.path.exists(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe")
    elif browser == "BRAVE":
        return os.path.exists(r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe") or \
            os.path.exists(r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe")
    return False


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


def _handle_reset_option(db_service) -> bool:
    """Gerencia opção de reset ou continuação"""
    try:
        # Verificar se há dados existentes
        stats = db_service.get_statistics()

        if stats and (stats.get('empresas_total', 0) > 0 or stats.get('termos_concluidos', 0) > 0):
            print("\n[INFO] Dados existentes encontrados:")
            print(f"  - Empresas: {stats.get('empresas_total', 0)}")
            print(f"  - E-mails: {stats.get('emails_total', 0)}")
            print(f"  - Telefones: {stats.get('telefones_total', 0)}")
            print(f"  - Progresso: {stats.get('progresso_pct', 0)}%")
            print()

            while True:
                opcao = input("[ESCOLHA] (C)ontinuar busca ou (R)esetar tudo? (C/R): ").upper().strip()

                if opcao == 'C':
                    print("[INFO] Continuando busca de onde parou...")
                    return True
                elif opcao == 'R':
                    print("[INFO] Resetando todos os dados...")
                    db_service.reset_data(confirm=True)
                    print("[OK] Reset concluído! Começando do zero...")
                    return True
                else:
                    print("[ERRO] Opção inválida. Digite C para continuar ou R para resetar.")
        else:
            print("[INFO] Nenhum dado anterior encontrado. Iniciando nova coleta...")
            return True

    except Exception as e:
        print(f"[ERRO] Falha ao verificar dados existentes: {e}")
        return True


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

        # Após criação das tabelas, executar carga inicial via InitialDataService (população controlada pela aplicação)
        try:
            from src.infrastructure.logging.initial_load_logger import load_logger
            from src.application.services.initial_data_application_service import InitialDataApplicationService
            init_svc = InitialDataApplicationService()
            load_logger.info('Iniciando população inicial via InitialDataService...')
            zones_count = init_svc.populate_zones()
            load_logger.info(f'Zonas populadas: {zones_count}')
            terms_count = init_svc.populate_base_terms()
            load_logger.info(f'Termos base populados: {terms_count}')
            zip_ok = init_svc.ensure_zip_seed()
            load_logger.info(f'TB_CEP_CONFIG garantida/seed: {zip_ok}')


        except Exception as e:
            # Log full stacktrace to the initial load log for debugging
            try:
                from src.infrastructure.logging.initial_load_logger import load_logger
                import traceback
                load_logger.error(f'Falha na população inicial: {e}\n{traceback.format_exc()}')
            except Exception:
                print(f'[AVISO] Falha na população inicial via InitialDataService: {e}')
                pass

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

        print("[INFO] Gerando termos de busca...")
        terms_count = db_service.initialize_search_terms()

        if terms_count == 0:
            print("[ERRO] Falha ao inicializar termos de busca")
            return 1

        mode_text = "TESTE" if config.is_test_mode else "PRODUÇÃO"
        print(f"[OK] {terms_count} termos de busca gerados (modo {mode_text})")
        # Log the source of terms (db / base_testes / base_busca / static_fallback)
        try:
            src = getattr(db_service, 'last_terms_source', None)
            if src == 'db':
                print('[INFO] Origem dos termos: TB_BASE_BUSCA (termos ativos no banco)')
            elif src == 'base_testes':
                print('[INFO] Origem dos termos: BASE_TESTES (modo de teste)')
            elif src == 'base_busca':
                print('[INFO] Origem dos termos: BASE_BUSCA (modo produção)')
            elif src == 'static_fallback':
                print('[INFO] Origem dos termos: fallback estático')
            else:
                print(f'[INFO] Origem dos termos: desconhecida ({src})')
        except Exception:
            pass

    except Exception as e:
        print(f"[ERRO] Falha ao conectar com banco: {e}")
        print("[INFO] Tentando recriar banco...")
        
        # Tentar recriar banco
        if _create_database_automatically():
            try:
                db_service = DatabaseApplicationService()
                terms_count = db_service.initialize_search_terms()
                print(f"[OK] Banco recriado com {terms_count} termos")
            except Exception as e2:
                print(f"[ERRO] Falha mesmo após recriar: {e2}")
                return 1
        else:
            print("[ERRO] Não foi possível recriar o banco")
            return 1

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