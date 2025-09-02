#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROBO 2 – COLETOR DE E-MAILS (ELEVADORES primeiro)
Ponto de entrada principal do robô
"""
import sys
from src.__version__ import __version__

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
    
    # Aplicação funciona 24h - sem limitação de horário
    collector_service = EmailApplicationService()
    
    try:
        success = collector_service.execute()
        
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