"""
Entidade Company - Representa uma empresa coletada
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class CompanyModel:
    """Entidade Empresa (rich model usado por repositories/services)"""
    id_empresa: Optional[int] = None
    name: Optional[str] = None
    emails: Optional[str] = None  # String com e-mails separados por ;
    domain: Optional[str] = None
    url: Optional[str] = None
    search_term: Optional[str] = ""
    address: Optional[str] = ""
    phone: Optional[str] = ""
    html_content: Optional[str] = ""
    id_termo: Optional[int] = None

    @classmethod
    def from_row(cls, row: Dict[str, Any]):
        if not isinstance(row, dict):
            return cls()
        lower = {k.lower(): v for k, v in row.items()}
        return cls(
            id_empresa=lower.get('id_empresa') or lower.get('id') or lower.get('id_empresa'),
            name=lower.get('nome') or lower.get('name') or lower.get('nome_empresa'),
            emails=lower.get('emails') or lower.get('email') or lower.get('emails'),
            domain=lower.get('dominio') or lower.get('domain'),
            url=lower.get('site_url') or lower.get('url') or lower.get('site'),
            search_term=lower.get('search_term') or lower.get('termo') or '',
            address=lower.get('address') or lower.get('endereco') or '',
            phone=lower.get('phone') or lower.get('telefone') or '',
            html_content=lower.get('html_content') or lower.get('html') or '',
            id_termo=lower.get('id_termo')
        )

    def to_api_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id_empresa,
            'nome': self.name,
            'emails': self.emails,
            'domain': self.domain,
            'url': self.url,
            'id_termo': self.id_termo
        }

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)
