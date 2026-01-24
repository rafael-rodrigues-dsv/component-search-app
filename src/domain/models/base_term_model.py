"""
Modelo para registros em TB_BASE_BUSCA
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class BaseTermModel:
    id_base: Optional[int] = None
    termo_busca: str = ""
    categoria: str = ""
    ativo: Optional[bool] = None
    data_criacao: Optional[str] = None
    is_test: Optional[bool] = None

    @classmethod
    def from_row(cls, row: Dict[str, Any]):
        if not isinstance(row, dict):
            return cls()
        lower = {k.lower(): v for k, v in row.items()}
        # 'ATIVO' in Access often stores -1 for true; normalize
        ativo = lower.get('ativo')
        if isinstance(ativo, int):
            ativo_bool = ativo != 0
        elif isinstance(ativo, str):
            ativo_bool = ativo.lower() in ('-1','1','true','t','yes')
        else:
            ativo_bool = bool(ativo)

        return cls(
            id_base=lower.get('id_base') or lower.get('id'),
            termo_busca=lower.get('termo_busca') or lower.get('termo') or '',
            categoria=lower.get('categoria') or '',
            ativo=ativo_bool,
            data_criacao=lower.get('data_criacao'),
            is_test=lower.get('is_test')
        )

    def to_api_dict(self) -> Dict[str, Any]:
        return {
            'ID_BASE': self.id_base,
            'TERMO_BUSCA': self.termo_busca,
            'CATEGORIA': self.categoria,
            'ATIVO': self.ativo
        }

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)
