"""
Domain Model: Estado de uma thread de coleta
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class CollectionThreadState:
    """Estado de uma thread de coleta individual"""

    thread_id: int
    term: str
    status: str  # 'pending', 'running', 'completed', 'stopped', 'error'
    progress: int = 0  # 0-100
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    companies_found: int = 0
    current_action: str = ""

    def start(self):
        """Marca thread como iniciada"""
        self.status = 'running'
        self.start_time = datetime.now()

    def complete(self):
        """Marca thread como concluída"""
        self.status = 'completed'
        self.end_time = datetime.now()
        self.progress = 100

    def stop(self):
        """Marca thread como parada"""
        self.status = 'stopped'
        self.end_time = datetime.now()

    def error(self, message: str):
        """Marca thread com erro"""
        self.status = 'error'
        self.end_time = datetime.now()
        self.error_message = message

    def update_progress(self, progress: int, action: str = ""):
        """Atualiza progresso e ação atual"""
        self.progress = min(100, max(0, progress))
        if action:
            self.current_action = action

    def to_dict(self) -> dict:
        """Converte para dicionário para JSON"""
        return {
            'thread_id': self.thread_id,
            'term': self.term,
            'status': self.status,
            'progress': self.progress,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'error_message': self.error_message,
            'companies_found': self.companies_found,
            'current_action': self.current_action,
            'duration_seconds': (
                (self.end_time - self.start_time).total_seconds()
                if self.start_time and self.end_time else None
            )
        }


@dataclass
class CollectionState:
    """Estado global do processamento multi-thread"""

    is_running: bool = False
    should_stop: bool = False
    max_workers: int = 0  # Deve ser configurado via ConfigManager (search.multi_threading.max_workers)
    threads: dict = field(default_factory=dict)  # {thread_id: CollectionThreadState}
    pending_terms: list = field(default_factory=list)
    active_threads: int = 0

    # Configurações da UI
    browser: str = 'CHROME'
    engine: str = 'GOOGLE'
    headless: bool = False

    def to_dict(self) -> dict:
        """Converte para dicionário para JSON"""
        return {
            'is_running': self.is_running,
            'should_stop': self.should_stop,
            'max_workers': self.max_workers,
            'active_threads': self.active_threads,
            'pending_terms_count': len(self.pending_terms),
            'threads': {tid: thread.to_dict() for tid, thread in self.threads.items()},
            'total_companies_found': sum(t.companies_found for t in self.threads.values()),
            'browser': self.browser,
            'engine': self.engine,
            'headless': self.headless
        }
