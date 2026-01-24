"""
Model for TB_ZONAS
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class ZoneModel:
    id_zona: Optional[int] = None
    nome: Optional[str] = None
    uf: Optional[str] = None

    @classmethod
    def from_row(cls, row: Dict[str, Any]):
        if not isinstance(row, dict):
            return cls()
        lower = {k.lower(): v for k, v in row.items()}
        return cls(id_zona=lower.get('id_zona') or lower.get('id'), nome=lower.get('nome'), uf=lower.get('uf'))

    def to_api_dict(self) -> Dict[str, Any]:
        return {'id': self.id_zona, 'name': self.nome, 'uf': self.uf}

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)
