"""
DashboardCache: cache simples em memória usado pelos endpoints do dashboard.
Armazena os resumos/statísticas para evitar queries frequentes ao Access DB.
"""
from threading import Lock
from typing import Any, Dict, Optional
from datetime import datetime, timezone


class DashboardCache:
    """Singleton leve para armazenar dados usados pelos widgets do dashboard.

    Uso:
        cache = DashboardCache.get_instance()
        cache.set('stats', {...})
        stats = cache.get('stats')
    """

    _instance = None

    def __init__(self):
        self._lock = Lock()
        self._data: Dict[str, Any] = {}
        self._updated: Dict[str, datetime] = {}

    @classmethod
    def get_instance(cls) -> "DashboardCache":
        if cls._instance is None:
            cls._instance = DashboardCache()
        return cls._instance

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._data[key] = value
            self._updated[key] = datetime.now(timezone.utc)

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            return self._data.get(key)

    def get_updated_at(self, key: str) -> Optional[datetime]:
        with self._lock:
            return self._updated.get(key)

    def clear(self, key: Optional[str] = None) -> None:
        with self._lock:
            if key is None:
                self._data.clear()
                self._updated.clear()
            else:
                self._data.pop(key, None)
                self._updated.pop(key, None)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._data)
