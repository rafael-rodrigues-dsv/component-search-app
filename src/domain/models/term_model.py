"""
Modelo para registros em TB_TERMOS_BUSCA
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class TermModel:
    id_termo: Optional[int] = None
    id_base: Optional[int] = None
    termo_completo: str = ""
    tipo_localizacao: str = ""
    status_processamento: str = ""
    data_criacao: Optional[str] = None
    data_processamento: Optional[str] = None

    @classmethod
    def from_row(cls, row: Dict[str, Any]):
        """Converte uma linha retornada pelo AccessRepository (dict com chaves possivelmente em maiúsculas)
        para um TermModel. Aceita tanto dicionários com chaves originais (EX.: 'ID_TERMO') quanto
        chaves em snake_case ou lowercase.
        """
        if not isinstance(row, dict):
            return cls()

        # Normalize keys to lowercase without accents for safer access
        lower = {k.lower(): v for k, v in row.items()}

        return cls(
            id_termo=lower.get('id_termo') or lower.get('id'),
            id_base=lower.get('id_base'),
            termo_completo=lower.get('termo_completo') or lower.get('termo') or lower.get('termo_busca') or '',
            tipo_localizacao=lower.get('tipo_localizacao') or lower.get('tipo') or '',
            status_processamento=lower.get('status_processamento') or lower.get('status') or '',
            data_criacao=lower.get('data_criacao'),
            data_processamento=lower.get('data_processamento')
        )

    def to_api_dict(self) -> Dict[str, Any]:
        """Serializa o modelo para o formato JSON esperado pelo front (compatibilidade com as chaves atuais).
        Retorna chaves em maiúsculo para manter comportamento legado: 'ID_BASE','TERMO_BUSCA','CATEGORIA', ...
        """
        api = {
            'ID_TERMO': self.id_termo,
            'ID_BASE': self.id_base,
            'TERMO_BUSCA': self.termo_completo,
            'TIPO_LOCALIZACAO': self.tipo_localizacao,
            'STATUS_PROCESSAMENTO': self.status_processamento,
            'DATA_CRIACAO': self.data_criacao,
            'DATA_PROCESSAMENTO': self.data_processamento
        }
        # remove keys with None for cleaner JSON
        return {k: v for k, v in api.items() if v is not None}

    def as_dict(self) -> Dict[str, Any]:
        """Retorna representação em snake_case (útil internamente)."""
        return asdict(self)
