"""
Serviço de configuração do usuário
"""


class UserConfigService:
    """Gerencia configurações do usuário via console"""

    @staticmethod
    def _check_browser_availability(browser: str) -> bool:
        """Verifica se o navegador está disponível"""
        import os
        if browser == "CHROME":
            return os.path.exists(r"C:\Program Files\Google\Chrome\Application\chrome.exe") or \
                os.path.exists(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe")
        elif browser == "BRAVE":
            return os.path.exists(r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe") or \
                os.path.exists(r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe")
        return False

    @staticmethod
    def get_browser() -> str:
        """Obtém navegador escolhido pelo usuário"""
        # Verifica disponibilidade
        chrome_available = UserConfigService._check_browser_availability("CHROME")
        brave_available = UserConfigService._check_browser_availability("BRAVE")

        # Se só um disponível, usa automaticamente
        if chrome_available and not brave_available:
            print("[INFO] Usando Google Chrome (único disponível)")
            return "CHROME"
        elif brave_available and not chrome_available:
            print("[INFO] Usando Brave Browser (único disponível)")
            return "BRAVE"

        # Se ambos disponíveis, pergunta
        while True:
            try:
                print("\n🌐 Escolha o navegador:")
                if chrome_available:
                    print("1. Google Chrome")
                if brave_available:
                    print("2. Brave Browser")

                option = input("Digite sua opção (1/2 - padrão: 1): ").strip()

                if not option or option == '1':
                    if chrome_available:
                        return "CHROME"
                    else:
                        print("[ERRO] Opção inválida")
                        continue
                elif option == '2':
                    if brave_available:
                        return "BRAVE"
                    else:
                        print("[ERRO] Opção inválida")
                        continue
                else:
                    print("[ERRO] Digite '1' para Chrome ou '2' para Brave")
            except:
                print("[ERRO] Entrada inválida")

    @staticmethod
    def get_search_engine() -> str:
        """Obtém motor de busca escolhido pelo usuário"""
        while True:
            try:
                print("\n🔍 Escolha o motor de busca:")
                print("1. Google")
                print("2. DuckDuckGo")
                option = input("Digite sua opção (1/2 - padrão: 1): ").strip()

                if not option or option == '1':
                    return "GOOGLE"
                elif option == '2':
                    return "DUCKDUCKGO"
                else:
                    print("[ERRO] Digite '1' para Google ou '2' para DuckDuckGo")
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
