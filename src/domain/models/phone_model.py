"""
Model for TB_TELEFONES
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class PhoneModel:
    id_phone: Optional[int] = None
    id_empresa: Optional[int] = None
    telefone: Optional[str] = None
    telefone_formatado: Optional[str] = None
    ddd: Optional[str] = None
    tipo: Optional[str] = None

    @classmethod
    def from_row(cls, row: Dict[str, Any]):
        if not isinstance(row, dict):
            return cls()
        lower = {k.lower(): v for k, v in row.items()}
        return cls(
            id_phone=lower.get('id_telefone') or lower.get('id') or lower.get('id_telefone'),
            id_empresa=lower.get('id_empresa'),
            telefone=lower.get('telefone') or lower.get('numero'),
            telefone_formatado=lower.get('telefone_formatado') or lower.get('formatted'),
            ddd=lower.get('ddd'),
            tipo=lower.get('tipo_telefone') or lower.get('tipo')
        )

    def to_api_dict(self) -> Dict[str, Any]:
        return {'id': self.id_phone, 'empresa_id': self.id_empresa, 'telefone': self.telefone, 'formatted': self.telefone_formatado, 'ddd': self.ddd, 'tipo': self.tipo}

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)
