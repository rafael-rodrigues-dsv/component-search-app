"""
Gerenciador de dados e limpeza
"""
import os
from config.settings import *

class DataManager:
    """Gerencia limpeza e inicialização de dados"""
    
    @staticmethod
    def clear_all_data():
        """Limpa todos os arquivos de dados"""
        os.makedirs(DATA_DIR, exist_ok=True)
        
        files_to_clear = [VISITED_JSON, SEEN_EMAILS_JSON, OUTPUT_XLSX]
        
        for file_path in files_to_clear:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"[INFO] Arquivo {file_path} removido")
            except Exception as e:
                print(f"[AVISO] Erro ao remover {file_path}: {e}")
        
        print("[OK] Dados anteriores limpos. Iniciando do zero...")