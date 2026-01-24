"""
Model for TB_CIDADES records
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class CityModel:
    id_cidade: Optional[int] = None
    nome: str = ''
    uf: str = ''
    ativo: Optional[bool] = None

    @classmethod
    def from_row(cls, row: Dict[str, Any]):
        if not isinstance(row, dict):
            return cls()
        lower = {k.lower(): v for k, v in row.items()}
        ativo = lower.get('ativo')
        if isinstance(ativo, int):
            ativo_bool = ativo != 0
        elif isinstance(ativo, str):
            ativo_bool = ativo.lower() in ('-1','1','true','t','yes')
        else:
            ativo_bool = bool(ativo)
        return cls(
            id_cidade=lower.get('id_cidade') or lower.get('id') or lower.get('id_cidade'),
            nome=lower.get('nome') or lower.get('nome_cidade') or lower.get('name') or '',
            uf=(lower.get('uf') or '').strip() if isinstance(lower.get('uf'), str) else lower.get('uf')
        )

    def to_api_dict(self) -> Dict[str, Any]:
        return {'id': self.id_cidade, 'name': self.nome, 'uf': self.uf}

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)
