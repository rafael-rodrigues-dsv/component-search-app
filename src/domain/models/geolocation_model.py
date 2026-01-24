"""
Model for geolocation records (TB_GEOLOCALIZACAO)
"""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any


@dataclass
class GeolocationModel:
    id_geo: Optional[int] = None
    id_empresa: Optional[int] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    status: Optional[str] = None

    @classmethod
    def from_row(cls, row: Dict[str, Any]):
        if not isinstance(row, dict):
            return cls()
        lower = {k.lower(): v for k, v in row.items()}
        return cls(
            id_geo=lower.get('id_geolocalizacao') or lower.get('id') or None,
            id_empresa=lower.get('id_empresa'),
            lat=lower.get('latitude') or lower.get('lat'),
            lon=lower.get('longitude') or lower.get('lon'),
            status=lower.get('status_processamento') or lower.get('status')
        )

    def to_api_dict(self) -> Dict[str, Any]:
        return {'id': self.id_geo, 'empresa_id': self.id_empresa, 'lat': self.lat, 'lon': self.lon, 'status': self.status}

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)
