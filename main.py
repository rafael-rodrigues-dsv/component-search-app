#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROBO 2 – COLETOR DE E-MAILS (ELEVADORES primeiro)
Ponto de entrada principal do robô
"""
import sys
from src.__version__ import __version__

from src.application.services.email_application_service import EmailApplicationService


def main():
    """Função principal do robô"""
    print(f"[INFO] Iniciando ROBO 2 - COLETOR DE E-MAILS (ELEVADORES) v{__version__}")
    
    # Verificar horário de funcionamento
    from src.domain.services.email_domain_service import WorkingHoursService
    working_hours = WorkingHoursService(8, 22)
    
    ignore_working_hours = False
    
    # Só pergunta se estiver fora do horário
    if not working_hours.is_working_time():
        from config.settings import OUT_OF_HOURS_WAIT_SECONDS
        import time
        
        # Primeira vez pergunta, depois só informa
        if not hasattr(main, '_asked_once'):
            response = input("[INFO] Fora do horário padrão (8:00–22:00). Executar mesmo assim? (S/N): ").strip().upper()
            if response == 'S':
                ignore_working_hours = True
            else:
                main._asked_once = True
                print("[INFO] Fora do horário padrão (8:00–22:00)")
                print()
                for i in range(OUT_OF_HOURS_WAIT_SECONDS, 0, -1):
                    print(f"\r[INFO] Próxima verificação em: {i}s", end="", flush=True)
                    time.sleep(1)
                print()
                return main()
        else:
            print("[INFO] Fora do horário padrão (8:00–22:00)")
            print()
            for i in range(OUT_OF_HOURS_WAIT_SECONDS, 0, -1):
                print(f"\r[INFO] Próxima verificação em: {i}s", end="", flush=True)
                time.sleep(1)
            print()
            return main()
    
    collector_service = EmailApplicationService(ignore_working_hours)
    
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