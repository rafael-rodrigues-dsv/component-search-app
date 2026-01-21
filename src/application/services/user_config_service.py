"""
Serviço de configuração do usuário
"""


class UserConfigService:
    """Gerencia configurações do usuário via console"""

    # Overrides (definidos em runtime pela UI)
    _browser_override: str = None
    _search_engine_override: str = None
    _processing_mode_override: int = None
    _headless_override: bool | None = None

    @staticmethod
    def set_browser(value: str):
        UserConfigService._browser_override = value

    @staticmethod
    def set_search_engine(value: str):
        UserConfigService._search_engine_override = value

    @staticmethod
    def set_processing_mode(value: int):
        UserConfigService._processing_mode_override = value

    @staticmethod
    def set_headless(value: bool) -> None:
        """Override via UI para executar o navegador em modo headless (True/False)."""
        UserConfigService._headless_override = bool(value)

    @staticmethod
    def get_headless() -> bool | None:
        """Retorna override do headless se definido; caso contrário None para usar config padrão."""
        return UserConfigService._headless_override

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

    # Novos helpers para uso da UI
    @staticmethod
    def list_available_browsers() -> list:
        """Retorna lista de navegadores detectados no host (ordem preferencial).
        Exemplo de retorno: ['CHROME', 'BRAVE'] ou []
        """
        browsers = []
        try:
            if UserConfigService._check_browser_availability("CHROME"):
                browsers.append("CHROME")
            if UserConfigService._check_browser_availability("BRAVE"):
                browsers.append("BRAVE")
        except Exception:
            # Em caso de erro ao checar, fornecer lista vazia (a UI tratará o fallback)
            return []
        return browsers

    @staticmethod
    def get_default_browser_without_prompt() -> str:
        """Retorna o navegador a ser usado sem realizar prompts interativos.
        Usa override se definido; caso contrário escolhe entre navegadores detectados
        ou retorna 'CHROME' por padrão.
        """
        if UserConfigService._browser_override:
            return UserConfigService._browser_override

        avail = UserConfigService.list_available_browsers()
        if len(avail) == 1:
            return avail[0]
        if len(avail) > 1:
            # preferir CHROME quando disponível
            return "CHROME" if "CHROME" in avail else avail[0]
        # nenhum detectado, fallback seguro
        return "CHROME"

    @staticmethod
    def get_default_search_engine_without_prompt() -> str:
        """Retorna o motor padrão sem prompt (respeita override)."""
        if UserConfigService._search_engine_override:
            return UserConfigService._search_engine_override
        return "GOOGLE"

    @staticmethod
    def get_browser() -> str:
        """Obtém navegador escolhido pelo usuário"""
        # Return override if set
        if UserConfigService._browser_override:
            return UserConfigService._browser_override

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

        # Se nenhum disponível, não ficar pedindo no console: retornar CHROME como padrão
        if not chrome_available and not brave_available:
            print("[AVISO] Nenhum navegador detectado; usando padrão: Google Chrome")
            return "CHROME"

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
        # Override
        if UserConfigService._search_engine_override:
            return UserConfigService._search_engine_override

        # Se não há stdin interativo (ex: executado via servidor web), retornar padrão sem prompt
        try:
            import sys
            if not sys.stdin or not sys.stdin.isatty():
                return "GOOGLE"
        except Exception:
            return "GOOGLE"

        # Interativo: pedir escolha
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
        """Retorna modo completo (sempre coleta tudo)"""
        # Override
        if UserConfigService._processing_mode_override is not None:
            return UserConfigService._processing_mode_override
        print("\n🔍 Modo de processamento: COMPLETO (coleta todos os resultados)")
        return 999999
