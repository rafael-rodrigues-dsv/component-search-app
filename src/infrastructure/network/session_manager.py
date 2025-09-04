"""
Gerenciador de Sessão para evitar detecção prolongada
"""
import random
import time
from typing import Optional


class SessionManager:
    """Gerencia sessões do navegador para evitar detecção"""
    
    def __init__(self, driver_manager):
        self.driver_manager = driver_manager
        self.session_start_time = time.time()
        self.searches_in_session = 0
        self.max_session_duration = random.uniform(1800, 3600)  # 30-60 min
        self.max_searches_per_session = random.randint(20, 40)
        
    def should_restart_session(self) -> bool:
        """Verifica se deve reiniciar a sessão"""
        current_time = time.time()
        session_duration = current_time - self.session_start_time
        
        # Critérios para reiniciar sessão
        if (session_duration > self.max_session_duration or 
            self.searches_in_session > self.max_searches_per_session):
            return True
            
        # Chance aleatória de reiniciar (simula comportamento humano)
        if random.random() < 0.05:  # 5% chance a cada verificação
            return True
            
        return False
    
    def restart_session(self) -> bool:
        """Reinicia a sessão do navegador"""
        try:
            print("[INFO] Reiniciando sessão para evitar detecção...")
            
            # Fecha navegador atual
            self.driver_manager.close_driver()
            
            # Pausa entre sessões (simula usuário saindo e voltando)
            break_time = random.uniform(30, 120)  # 30s-2min
            print(f"[INFO] Pausa entre sessões: {break_time:.1f}s")
            time.sleep(break_time)
            
            # Inicia nova sessão
            if self.driver_manager.start_driver():
                self.session_start_time = time.time()
                self.searches_in_session = 0
                self.max_session_duration = random.uniform(1800, 3600)
                self.max_searches_per_session = random.randint(20, 40)
                print("[INFO] Nova sessão iniciada com sucesso")
                return True
            else:
                print("[ERRO] Falha ao iniciar nova sessão")
                return False
                
        except Exception as e:
            print(f"[ERRO] Erro ao reiniciar sessão: {e}")
            return False
    
    def increment_search_count(self) -> None:
        """Incrementa contador de buscas da sessão"""
        self.searches_in_session += 1
    
    def get_session_info(self) -> dict:
        """Retorna informações da sessão atual"""
        current_time = time.time()
        return {
            "duration": current_time - self.session_start_time,
            "searches": self.searches_in_session,
            "max_duration": self.max_session_duration,
            "max_searches": self.max_searches_per_session
        }