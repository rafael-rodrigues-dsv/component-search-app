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
    
    # Verificar horário de funcionamento
    from src.domain.email_processor import WorkingHoursService
    working_hours = WorkingHoursService(8, 22)
    
    if not working_hours.is_working_time():
        from config.settings import OUT_OF_HOURS_WAIT_SECONDS
        import time
        
        # Primeira vez pergunta, depois só informa
        if not hasattr(main, '_asked_once'):
            response = input("[INFO] Fora do horário padrão (8:00–22:00). Executar mesmo assim? (S/N): ").strip().upper()
            if response == 'S':
                return  # Continua execução
            main._asked_once = True
        
        print("[INFO] Fora do horário padrão (8:00–22:00)")
        print()
        for i in range(OUT_OF_HOURS_WAIT_SECONDS, 0, -1):
            print(f"\r[INFO] Próxima verificação em: {i}s", end="", flush=True)
            time.sleep(1)
        print()  # Nova linha
        return main()  # Recheca recursivamente
    
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