"""
Model for TB_EMAILS
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class EmailModel:
    id_email: Optional[int] = None
    id_empresa: Optional[int] = None
    email: Optional[str] = None
    dominio_email: Optional[str] = None
    validado: Optional[bool] = None

    @classmethod
    def from_row(cls, row: Dict[str, Any]):
        if not isinstance(row, dict):
            return cls()
        lower = {k.lower(): v for k, v in row.items()}
        valid = lower.get('validado')
        if isinstance(valid, int):
            valid_bool = valid != 0
        else:
            valid_bool = bool(valid)
        return cls(
            id_email=lower.get('id_email') or lower.get('id') or lower.get('id_email'),
            id_empresa=lower.get('id_empresa'),
            email=lower.get('email'),
            dominio_email=lower.get('dominio_email') or lower.get('dominio'),
            validado=valid_bool
        )

    def to_api_dict(self) -> Dict[str, Any]:
        return {'id': self.id_email, 'empresa_id': self.id_empresa, 'email': self.email, 'dominio': self.dominio_email, 'validado': self.validado}

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)
