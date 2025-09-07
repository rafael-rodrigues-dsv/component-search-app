#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python Search App - Coletor de E-mails e Contatos
Ponto de entrada principal da aplicação
"""
import sys
from pathlib import Path

from src.__version__ import __version__
from src.application.services.database_service import DatabaseService
from src.application.services.email_application_service import EmailApplicationService


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

                    # Recarregar dados iniciais
                    print("[INFO] Recarregando dados iniciais...")
                    import subprocess
                    
                    script_path = Path("scripts/database/load_initial_data.py")
                    subprocess.run([sys.executable, str(script_path)], 
                                 capture_output=True, encoding='utf-8', errors='ignore')

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
    
    # Mostrar modo de operação
    mode_text = "TESTE" if config.is_test_mode else "PRODUÇÃO"
    print(f"[INFO] Iniciando Python Search App - Coletor de E-mails e Contatos v{__version__}")
    print(f"[INFO] Modo de operação: {mode_text}")

    # Verificar se pelo menos um navegador está disponível
    chrome_available = _check_browser_availability("CHROME")
    brave_available = _check_browser_availability("BRAVE")

    if not chrome_available and not brave_available:
        print("[ERRO] Nenhum navegador suportado encontrado!")
        print("[INFO] Instale pelo menos um dos navegadores:")
        print("  - Google Chrome: https://www.google.com/chrome/")
        print("  - Brave Browser: https://brave.com/")
        input("Pressione Enter para sair...")
        return 1

    # Formata lista de navegadores disponíveis
    browsers = []
    if chrome_available:
        browsers.append("Google Chrome")
    if brave_available:
        browsers.append("Brave Browser")

    if len(browsers) == 1:
        print(f"[OK] Navegador disponível: {browsers[0]}")
    else:
        print(f"[OK] Navegadores disponíveis: {', '.join(browsers)}")

    # Verificar se banco Access existe
    db_path = Path("data/pythonsearch.accdb")

    if not db_path.exists():
        print("[INFO] Banco Access não encontrado. Criando automaticamente...")
        if not _create_database_automatically():
            print("[ERRO] Falha ao criar banco de dados")
            input("Pressione Enter para sair...")
            return 1
        print("[OK] Banco criado com sucesso!")

    # Inicializar banco de dados
    print("[INFO] Inicializando banco de dados...")
    print("[INFO] Conectando ao banco Access...")
    
    try:
        # Inicializar singleton de banco no início
        from src.infrastructure.repositories.access_repository import AccessRepository
        db_repository = AccessRepository()  # Cria singleton
        
        db_service = DatabaseService()
        print("[OK] Conexão singleton estabelecida com sucesso")
        
        print("[INFO] Gerando termos de busca...")
        terms_count = db_service.initialize_search_terms()
        
        if terms_count == 0:
            print("[ERRO] Falha ao inicializar termos de busca")
            input("Pressione Enter para sair...")
            return 1
        
        mode_text = "TESTE" if config.is_test_mode else "PRODUÇÃO"
        print(f"[OK] {terms_count} termos de busca gerados (modo {mode_text})")
        
    except Exception as e:
        print(f"[ERRO] Falha ao conectar com banco: {e}")
        print("[INFO] Tentando recriar banco...")
        
        # Tentar recriar banco
        if _create_database_automatically():
            try:
                db_service = DatabaseService()
                terms_count = db_service.initialize_search_terms()
                print(f"[OK] Banco recriado com {terms_count} termos")
            except Exception as e2:
                print(f"[ERRO] Falha mesmo após recriar: {e2}")
                input("Pressione Enter para sair...")
                return 1
        else:
            print("[ERRO] Não foi possível recriar o banco")
            input("Pressione Enter para sair...")
            return 1

    # Escolher modo de operação
    print("\n=== PYTHON SEARCH APP ===")
    print("[1] Processar coleta de dados (e-mails e telefones)")
    print("[2] Enriquecer endereços (ViaCEP)")
    print("[3] Processar geolocalização (Nominatim)")
    print("[4] Extrair planilha Excel")
    print("[5] Sair")

    while True:
        opcao = input("\nEscolha uma opção (1-5): ").strip()

        if opcao == '1':
            # Verificar se precisa resetar ou continuar APENAS para coleta
            if not _handle_reset_option(db_service):
                break
            print("\n[INFO] Iniciando coleta de dados otimizada...")
            collector_service = EmailApplicationService()
            success = collector_service.execute()
            break
        elif opcao == '2':
            print("\n[INFO] Iniciando enriquecimento de endereços via ViaCEP...")
            from src.application.services.cep_enrichment_application_service import CepEnrichmentApplicationService
            cep_service = CepEnrichmentApplicationService()

            # Mostrar estatísticas antes
            stats = cep_service.get_cep_enrichment_stats()
            print(f"\n[INFO] Tarefas CEP: {stats['total']}")
            print(f"[INFO] Já processadas: {stats['concluidos']} ({stats['percentual']}%)")
            print(f"[INFO] Pendentes: {stats['pendentes']}")
            print(f"[INFO] Erros: {stats['erros']}")

            if stats['pendentes'] == 0 and stats['total'] > 0:
                print("\n[OK] Todos os endereços já foram processados!")
                success = True
            else:
                # Criar tarefas se necessário
                if stats['total'] == 0:
                    print("\n[INFO] Criando tarefas de enriquecimento...")
                    created = cep_service.create_cep_enrichment_tasks()
                    if created == 0:
                        print("\n[AVISO] Nenhuma empresa com CEP encontrada!")
                        success = False
                        break
                
                result = cep_service.process_cep_enrichment()
                success = result['processadas'] > 0
                print(f"\n[OK] Processamento concluído: {result['enriquecidas']}/{result['total']} enriquecidas")
            break
        elif opcao == '3':
            print("\n[INFO] Iniciando processamento de geolocalização via Nominatim...")
            from src.application.services.geolocation_application_service import GeolocationApplicationService
            geo_service = GeolocationApplicationService()

            # Mostrar estatísticas antes
            stats = geo_service.get_geolocation_stats()
            print(f"\n[INFO] Empresas com endereço: {stats['total_com_endereco']}")
            print(f"[INFO] Já geocodificadas: {stats['geocodificadas']} ({stats['percentual']}%)")
            print(f"[INFO] Pendentes: {stats['pendentes']}")

            if stats['pendentes'] == 0:
                print("\n[OK] Todas as empresas já foram geocodificadas!")
                success = True
            else:
                result = geo_service.process_geolocation()
                success = result['geocodificadas'] > 0
                print(f"\n[OK] Processamento concluído: {result['geocodificadas']}/{result['total']} geocodificadas")
            break
        elif opcao == '4':
            print("\n[INFO] Extraindo planilha Excel...")
            from src.application.services.excel_application_service import ExcelApplicationService
            excel_service = ExcelApplicationService()

            # Mostrar estatísticas antes
            stats = excel_service.get_export_stats()
            print(f"\n[INFO] Empresas disponíveis: {stats['empresas_disponiveis']}")
            print(f"[INFO] E-mails disponíveis: {stats['emails_disponiveis']}")
            print(f"[INFO] Telefones disponíveis: {stats['telefones_disponiveis']}")

            if not stats['pode_exportar']:
                print("\n[AVISO] Nenhuma empresa com dados coletados encontrada!")
                success = False
            else:
                result = excel_service.export_excel()
                success = result['success']
                if success:
                    print(f"\n[OK] {result['message']} em {result['path']}")
                else:
                    print(f"\n[ERRO] {result['message']}")
            break
        elif opcao == '5':
            print("\n[INFO] Saindo...")
            return 0
        else:
            print("[ERRO] Opção inválida. Digite 1, 2, 3, 4 ou 5.")

    try:
        # Mostrar estatísticas finais
        if success:
            stats = db_service.get_statistics()
            if stats:
                print("\n[INFO] === ESTATÍSTICAS FINAIS ===")
                print(f"[INFO] Termos processados: {stats['termos_concluidos']}/{stats['termos_total']} ({stats['progresso_pct']}%)")
                print(f"[INFO] Empresas encontradas: {stats['empresas_total']}")
                print(f"[INFO] E-mails coletados: {stats['emails_total']}")
                print(f"[INFO] Telefones coletados: {stats['telefones_total']}")
                
                # Estatísticas de CEP enrichment
                try:
                    from src.application.services.cep_enrichment_application_service import CepEnrichmentApplicationService
                    cep_service = CepEnrichmentApplicationService()
                    cep_stats = cep_service.get_cep_enrichment_stats()
                    if cep_stats['total'] > 0:
                        print(f"[INFO] CEP enriquecidos: {cep_stats['concluidos']}/{cep_stats['total']} ({cep_stats['percentual']}%)")
                except:
                    pass
                
                # Estatísticas de geolocalização
                try:
                    from src.application.services.geolocation_application_service import GeolocationApplicationService
                    geo_service = GeolocationApplicationService()
                    geo_stats = geo_service.get_geolocation_stats()
                    if geo_stats['total_com_endereco'] > 0:
                        print(f"[INFO] Geocodificadas: {geo_stats['geocodificadas']}/{geo_stats['total_com_endereco']} ({geo_stats['percentual']}%)")
                except:
                    pass

        if success:
            print("[OK] Aplicação executada com sucesso")
        else:
            print("[ERRO] Falha na execução da aplicação")
            
        # Fechar conexão singleton
        try:
            from src.infrastructure.repositories.access_repository import AccessRepository
            AccessRepository().close_connection()
            print("[OK] Conexão singleton fechada")
        except:
            pass
        
        input("Pressione Enter para sair...")
        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n[INFO] Aplicação interrompida pelo usuário")
        # Fechar conexão singleton
        try:
            from src.infrastructure.repositories.access_repository import AccessRepository
            AccessRepository().close_connection()
        except:
            pass
        return 0

    except Exception as e:
        print(f"[ERRO] Erro inesperado: {e}")
        # Fechar conexão singleton
        try:
            from src.infrastructure.repositories.access_repository import AccessRepository
            AccessRepository().close_connection()
        except:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())