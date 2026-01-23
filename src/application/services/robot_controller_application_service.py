from threading import Event

# Módulo simples para controle de parada cooperativa do robô
_stop_event = Event()

def request_stop() -> None:
    """Sinaliza para o robô que deve parar o processamento o mais rápido possível."""
    _stop_event.set()

def clear_stop() -> None:
    """Limpa o sinal de parada (preparar para nova execução)."""
    _stop_event.clear()

def is_stop_requested() -> bool:
    """Retorna True se foi solicitado parada."""
    return _stop_event.is_set()
