import logging

# Logger de carga inicial: rely on root logger handlers and propagate so SocketIOLogHandler receives messages
_logger = logging.getLogger('initial_load')
_logger.setLevel(logging.DEBUG)
# Ensure messages propagate to root handlers (so SocketIOLogHandler attached to root will capture them)
_logger.propagate = True


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
