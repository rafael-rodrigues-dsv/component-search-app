"""
Sistema de Logging Transparente
================================

Mantém compatibilidade total com logs atuais (Google/DuckDuckGo)
"""


class ScraperLogger:
    """Sistema de logging padronizado para transparência"""

    # Emojis padronizados (compatível com logs atuais)
    EMOJI = {
        'search': '🔍',
        'web': '🌐',
        'keyboard': '⌨️',
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'link': '🔗',
        'document': '📄',
        'magnifier': '🔍',
        'email': '📧',
        'phone': '📞',
        'location': '📍',
        'building': '🏢',
        'back': '↩️',
        'clock': '⏱️',
        'robot': '🤖',
        'target': '🎯',
        'chart': '📊',
        'lightbulb': '💡',
        'fire': '🔥',
        'rocket': '🚀'
    }

    def __init__(self, scraper_name: str):
        """
        Args:
            scraper_name: Nome do scraper ('GOOGLE', 'DUCKDUCKGO', 'SCRAPER_V2', etc)
        """
        self.scraper_name = scraper_name
        self.indent_level = 0

    def indent(self):
        """Aumenta nível de indentação (para logs aninhados)"""
        self.indent_level += 1

    def dedent(self):
        """Diminui nível de indentação"""
        self.indent_level = max(0, self.indent_level - 1)

    def reset_indent(self):
        """Reseta indentação para nível 0"""
        self.indent_level = 0

    def log(self, emoji_key: str, message: str, force_prefix: str = None):
        """
        Log padronizado

        Args:
            emoji_key: Chave do emoji (ex: 'search', 'success', 'error')
            message: Mensagem a ser logada
            force_prefix: Força um prefixo diferente (opcional)
        """
        emoji = self.EMOJI.get(emoji_key, '')
        prefix = force_prefix or self.scraper_name
        indent = '  ' * self.indent_level
        print(f"{indent}[{prefix}] {emoji} {message}")

    def log_step(self, step_name: str, emoji_key: str = 'rocket'):
        """
        Log de início de passo (com indentação automática)

        Args:
            step_name: Nome do passo
            emoji_key: Emoji a usar (padrão: 'rocket')
        """
        emoji = self.EMOJI.get(emoji_key, '🚀')
        indent = '  ' * self.indent_level
        print(f"{indent}[{self.scraper_name}] {emoji} {step_name}")
        self.indent()

    def log_step_end(self, result_message: str = None, emoji_key: str = 'success'):
        """
        Log de fim de passo (com dedentação automática)

        Args:
            result_message: Mensagem de resultado (opcional)
            emoji_key: Emoji a usar (padrão: 'success')
        """
        self.dedent()
        if result_message:
            emoji = self.EMOJI.get(emoji_key, '✅')
            indent = '  ' * self.indent_level
            print(f"{indent}[{self.scraper_name}] {emoji} {result_message}")

    def log_phase(self, phase_name: str):
        """
        Log de fase (ex: CLASSIFICAÇÃO, EXTRAÇÃO)

        Args:
            phase_name: Nome da fase
        """
        print(f"\n{'='*60}")
        print(f"[{self.scraper_name}] 🎯 FASE: {phase_name}")
        print(f"{'='*60}\n")

    def log_fetch(self, url: str):
        """Log de fetch HTTP"""
        self.log('web', f"Acessando: {url[:60]}...")

    def log_html_captured(self, size: int):
        """Log de HTML capturado"""
        self.log('document', f"HTML: {size:,} chars")

    def log_classification(self, site_type: str, confidence: str):
        """Log de classificação"""
        self.log('target', f"Tipo: {site_type} | Confiança: {confidence}")

    def log_extraction_start(self):
        """Log início extração"""
        self.log('magnifier', "Extraindo dados...")

    def log_extraction_result(self, emails: int, phones: int, address: bool):
        """Log resultado extração"""
        self.log('email', f"Emails: {emails} encontrados")
        self.log('phone', f"Telefones: {phones} encontrados")
        if address:
            self.log('location', "Endereço: encontrado")

    def log_strategy(self, strategy_name: str):
        """Log estratégia aplicada"""
        self.log('robot', f"Estratégia: {strategy_name}")

    def log_budget(self, pages: int, time_ms: int):
        """Log de budget usado"""
        self.log('chart', f"Budget: {pages} páginas | {time_ms}ms")

    def log_success(self, company_name: str, domain: str):
        """Log de sucesso"""
        self.log('success', f"{company_name[:40]}... | {domain}")

    def log_error(self, error_msg: str):
        """Log de erro"""
        self.log('error', f"Erro: {error_msg[:60]}...")

    def log_performance(self, path: str, time_ms: int):
        """Log de performance"""
        self.log('clock', f"Path: {path} | Tempo: {time_ms}ms")

    def log_decision(self, decision: str, reason: str):
        """Log de decisão do sistema"""
        self.log('lightbulb', f"{decision} → {reason}")

    def indent(self):
        """Aumenta indentação"""
        self.indent_level += 1

    def dedent(self):
        """Diminui indentação"""
        if self.indent_level > 0:
            self.indent_level -= 1
