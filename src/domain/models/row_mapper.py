"""
Helpers para mapear rows (dict) retornadas pelo AccessRepository para dicionários normalizados
e para auxiliar os modelos `from_row` quando necessário.
"""
from typing import Dict, Any


def normalize_row_keys(row: Dict[str, Any]) -> Dict[str, Any]:
    """Garante chaves em lowercase e sem espaços, útil para conversão consistente."""
    if not isinstance(row, dict):
        return {}
    return {k.strip().lower(): v for k, v in row.items()}


def active_flag_to_bool(value: Any) -> bool:
    """Converte valores típicos de Access (0, -1, '0', '1', True/False) para bool."""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    try:
        s = str(value).strip()
        if s == '':
            return False
        if s.lower() in ('-1', '1', 'true', 't', 'yes'):
            return True
        if s == '0' or s.lower() in ('false', 'f', 'no', 'n'):
            return False
        # numeric fallback
        try:
            return int(s) != 0
        except Exception:
            return True
    except Exception:
        return False
