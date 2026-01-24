"""
Model for TB_CEP_ENRICHMENT tasks
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class CepEnrichmentModel:
    id_task: Optional[int] = None
    id_empresa: Optional[int] = None
    id_endereco: Optional[int] = None
    status: Optional[str] = None
    tentativas: Optional[int] = None

    @classmethod
    def from_row(cls, row: Dict[str, Any]):
        if not isinstance(row, dict):
            return cls()
        lower = {k.lower(): v for k, v in row.items()}
        return cls(
            id_task=lower.get('id_cep_enrichment') or lower.get('id') or lower.get('id_cep_enrichment'),
            id_empresa=lower.get('id_empresa'),
            id_endereco=lower.get('id_endereco'),
            status=lower.get('status_processamento') or lower.get('status'),
            tentativas=lower.get('tentativas')
        )

    def to_api_dict(self) -> Dict[str, Any]:
        return {'id': self.id_task, 'empresa_id': self.id_empresa, 'endereco_id': self.id_endereco, 'status': self.status, 'tentativas': self.tentativas}

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)
