#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROBO 2 – COLETOR DE E-MAILS (ELEVADORES primeiro)
Ponto de entrada principal do robô
"""
import sys
from src.application.email_robot_service import EmailCollectorService


def main():
    """Função principal do robô"""
    print("[INFO] Iniciando ROBO 2 - COLETOR DE E-MAILS (ELEVADORES)")
    
    collector_service = EmailCollectorService()
    
    try:
        success = collector_service.execute()
        
        if success:
            print("[OK] Robô executado com sucesso")
            print("[INFO] Encerrando automaticamente em 3 segundos...")
            import time
            time.sleep(3)
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