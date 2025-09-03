"""
Modelo para configuração de retry
"""
from dataclasses import dataclass


@dataclass
class RetryConfigModel:
    """Modelo para configuração de retry pattern"""
    max_attempts: int = 3
    base_delay: float = 1.0
    backoff_factor: float = 2.0
    max_delay: float = 60.0
