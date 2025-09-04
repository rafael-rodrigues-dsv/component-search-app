"""
Gerenciador de retry pattern para operações de rede
"""
import random
import time
from functools import wraps
from typing import Callable, Any, Type, Tuple

from src.domain.models.retry_config_model import RetryConfigModel


class RetryManager:
    """Gerenciador de retry pattern com backoff exponencial"""

    @staticmethod
    def with_retry(
            max_attempts: int = 3,
            base_delay: float = 1.0,
            backoff_factor: float = 2.0,
            max_delay: float = 60.0,
            exceptions: Tuple[Type[Exception], ...] = (Exception,)
    ):
        """Decorator para retry com backoff exponencial"""

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                last_exception = None

                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt == max_attempts - 1:
                            raise

                        # Calcula delay com backoff exponencial + jitter
                        delay = min(
                            base_delay * (backoff_factor ** attempt),
                            max_delay
                        )
                        jitter = random.uniform(0, delay * 0.1)
                        total_delay = delay + jitter

                        time.sleep(total_delay)

                if last_exception:
                    raise last_exception
                return None

            return wrapper

        return decorator

    @staticmethod
    def from_config(config: RetryConfigModel):
        """Cria decorator a partir de configuração"""
        return RetryManager.with_retry(
            max_attempts=config.max_attempts,
            base_delay=config.base_delay,
            backoff_factor=config.backoff_factor,
            max_delay=config.max_delay
        )
