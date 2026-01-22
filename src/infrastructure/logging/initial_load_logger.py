import logging
from pathlib import Path

# Logger de carga inicial: apenas saída no console (sem arquivo)
_logger = logging.getLogger('initial_load')
_logger.setLevel(logging.DEBUG)

# Prevent adding multiple handlers if module reloaded
if not _logger.handlers:
    # Console handler that mirrors the old style [LEVEL] message
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(message)s'))
    _logger.addHandler(ch)


class InitialLoadLogger:
    """Helper to write load-specific logs both to console and to a file.

    Methods mirror logging levels but format messages to look similar to existing
    console prints (e.g. "[INFO] Mensagem").
    """

    @staticmethod
    def _fmt(level: str, msg: str) -> str:
        return f"[LOAD][{level}] {msg}"

    @staticmethod
    def info(msg: str):
        _logger.info(InitialLoadLogger._fmt('INFO', msg))

    @staticmethod
    def debug(msg: str):
        _logger.debug(InitialLoadLogger._fmt('DEBUG', msg))

    @staticmethod
    def warning(msg: str):
        _logger.warning(InitialLoadLogger._fmt('WARN', msg))

    @staticmethod
    def error(msg: str):
        _logger.error(InitialLoadLogger._fmt('ERRO', msg))


# Expose a module-level instance
load_logger = InitialLoadLogger()
