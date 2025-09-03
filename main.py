#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROBO 2 – COLETOR DE E-MAILS (ELEVADORES primeiro)
Ponto de entrada principal do robô
"""
import sys
from src.__version__ import __version__

from src.application.services.email_application_service import EmailApplicationService
from src.application.services.database_service import DatabaseService


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
        import subprocess
        import sys
        from pathlib import Path
        
        # Executar script de criação do banco
        script_path = Path("scripts/database/create_db_simple.py")
        
        # Criar versão automática sem input
        import sys
        sys.path.append(str(Path("scripts/database")))
        from create_db_simple import create_simple_db
        
        # Executar função diretamente em modo automático
        create_simple_db(auto_mode=True)
        
        # Carregar dados iniciais
        try:
            script_path = Path("scripts/database/load_initial_data.py")
            result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[AVISO] Erro ao carregar dados iniciais: {result.stderr}")
                print("[INFO] Continuando com dados básicos já carregados...")
            return True  # Sempre retorna True pois o banco foi criado com dados básicos
        except Exception as e:
            print(f"[AVISO] Falha ao executar load_initial_data: {e}")
            print("[INFO] Continuando com dados básicos já carregados...")
            return True  # Banco foi criado com sucesso
        
    except Exception as e:
        print(f"[ERRO] Falha na criação automática: {e}")
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
                    import sys
                    from pathlib import Path
                    
                    script_path = Path("scripts/database/load_initial_data.py")
                    subprocess.run([sys.executable, str(script_path)], capture_output=True)
                    
                    print("[OK] Reset concluído! Começando do zero...")
                    return True
                else:
                    print("[ERRO] Opção inválida. Digite C para continuar ou R para resetar.")
        else:
            print("[INFO] Nenhum dado anterior encontrado. Iniciando nova coleta...")
            return True
            
    except Exception as e:
        print(f"[ERRO] Falha ao verificar dados existentes: {e}")
        return True  # Continua mesmo com erro


def main():
    """Função principal do robô"""
    print(f"[INFO] Iniciando ROBO 2 - COLETOR DE E-MAILS (ELEVADORES) v{__version__}")
    
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
    from pathlib import Path
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
    db_service = DatabaseService()
    
    # Verificar se precisa resetar ou continuar
    if not _handle_reset_option(db_service):
        return 0
    
    terms_count = db_service.initialize_search_terms()
    
    if terms_count == 0:
        print("[ERRO] Falha ao inicializar banco de dados")
        input("Pressione Enter para sair...")
        return 1
    
    # Aplicação funciona 24h - sem limitação de horário
    collector_service = EmailApplicationService()
    
    try:
        success = collector_service.execute()
        
        # Exportar para Excel após execução
        if success:
            print("[INFO] Exportando dados para Excel...")
            excel_success, count = db_service.export_to_excel()
            if excel_success:
                print(f"[OK] Excel gerado com {count} registros")
            
            # Mostrar estatísticas finais
            stats = db_service.get_statistics()
            if stats:
                print("\n[INFO] === ESTATÍSTICAS FINAIS ===")
                print(f"[INFO] Termos processados: {stats['termos_concluidos']}/{stats['termos_total']} ({stats['progresso_pct']}%)")
                print(f"[INFO] Empresas encontradas: {stats['empresas_total']}")
                print(f"[INFO] E-mails coletados: {stats['emails_total']}")
                print(f"[INFO] Telefones coletados: {stats['telefones_total']}")
        
        if success:
            print("[OK] Robô executado com sucesso")
            print("[INFO] Encerrando em:")
            import time
            for i in range(3, 0, -1):
                print(f"{i}")
                time.sleep(1)
            print("[INFO] Finalizando...")
            return 0
        else:
            print("[ERRO] Falha na execução do robô")
            input("Pressione Enter para sair...")
            return 1
            
    except KeyboardInterrupt:
        print("\n[INFO] Robô interrompido pelo usuário")
        return 0
        
    except Exception as e:
        print(f"[ERRO] Erro inesperado: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())