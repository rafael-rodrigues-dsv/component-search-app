"""
Serviço de configuração do usuário
"""

class UserConfigService:
    """Gerencia configurações do usuário via console"""
    
    @staticmethod
    def get_search_engine() -> str:
        """Obtém motor de busca escolhido pelo usuário"""
        while True:
            try:
                print("\n🔍 Escolha o motor de busca:")
                print("1. DuckDuckGo")
                print("2. Google Chrome")
                option = input("Digite sua opção (1/2 - padrão: 1): ").strip()
                
                if not option or option == '1':
                    return "DUCKDUCKGO"
                elif option == '2':
                    return "GOOGLE"
                else:
                    print("[ERRO] Digite '1' para DuckDuckGo ou '2' para Google Chrome")
            except:
                print("[ERRO] Entrada inválida")
    
    @staticmethod
    def get_restart_option() -> bool:
        """Obtém se deve reiniciar do zero"""
        while True:
            try:
                option = input("\n🔄 Reiniciar busca do zero? (s/n - padrão: n): ").lower().strip()
                if not option or option == 'n':
                    return False
                elif option == 's':
                    return True
                else:
                    print("[ERRO] Digite 's' para reiniciar ou 'n' para continuar")
            except:
                print("[ERRO] Entrada inválida")
    
    @staticmethod
    def get_processing_mode() -> int:
        """Obtém modo de processamento"""
        while True:
            try:
                mode = input("\n🔍 Processamento em lote ou completo? (l/c - padrão: c): ").lower().strip()
                if not mode or mode == 'c':
                    return 999999
                elif mode == 'l':
                    while True:
                        try:
                            limit = input("Quantos resultados por termo? (padrão: 10): ")
                            if not limit.strip():
                                return 10
                            limit = int(limit)
                            if limit > 0:
                                return limit
                            else:
                                print("[ERRO] Digite um número maior que zero")
                        except ValueError:
                            print("[ERRO] Digite um número válido")
                else:
                    print("[ERRO] Digite 'l' para lote ou 'c' para completo")
            except:
                print("[ERRO] Entrada inválida")