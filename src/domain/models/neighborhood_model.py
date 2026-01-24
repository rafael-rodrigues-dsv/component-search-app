"""
Model for TB_BAIRROS records
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class NeighborhoodModel:
    id_bairro: Optional[int] = None
    nome: str = ''
    uf: str = ''
    id_municipio: Optional[int] = None
    cidade: Optional[str] = None

    @classmethod
    def from_row(cls, row: Dict[str, Any]):
        if not isinstance(row, dict):
            return cls()
        lower = {k.lower(): v for k, v in row.items()}
        return cls(
            id_bairro=lower.get('id_bairro') or lower.get('id') or None,
            nome=lower.get('nome') or lower.get('nome_bairro') or '',
            uf=(lower.get('uf') or '').strip() if isinstance(lower.get('uf'), str) else lower.get('uf'),
            id_municipio=lower.get('id_municipio'),
            cidade=lower.get('cidade')
        )

    def to_api_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id_bairro,
            'name': self.nome,
            'uf': self.uf,
            'city': self.cidade,
            'municipio_id': self.id_municipio
        }

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)
