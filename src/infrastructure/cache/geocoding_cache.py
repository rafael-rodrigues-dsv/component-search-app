"""
Cache de Geocodificação - Reduz drasticamente chamadas ao Nominatim
Usa banco unificado pythonsearchcache.db
"""
import hashlib
import sqlite3
import time
from pathlib import Path
from typing import Optional, Tuple


class GeocodingCache:
    """Cache inteligente de coordenadas para evitar chamadas repetidas ao Nominatim"""

    def __init__(self):
        self.cache_dir = Path("data/cache")
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.db_path = self.cache_dir / "pythonsearchcache.db"  # ✅ Banco unificado
        # Tabela criada por scripts/database/create_cache_db.py

    def _hash_address(self, address: str) -> str:
        """Gera hash único do endereço normalizado"""
        normalized = address.lower().strip()
        normalized = ' '.join(normalized.split())  # Remove espaços extras
        return hashlib.md5(normalized.encode()).hexdigest()

    def get(self, address: str) -> Optional[Tuple[float, float]]:
        """Busca coordenadas no cache"""
        if not address:
            return None

        address_hash = self._hash_address(address)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("""
                SELECT latitude, longitude, hit_count
                FROM geocoding_cache 
                WHERE address_hash = ?
            """, (address_hash,))

            row = cursor.fetchone()

            if row:
                lat, lon, hit_count = row
                # Incrementa contador de hits
                conn.execute("""
                    UPDATE geocoding_cache 
                    SET hit_count = hit_count + 1 
                    WHERE address_hash = ?
                """, (address_hash,))
                conn.commit()
                conn.close()
                return (lat, lon)

            conn.close()
            return None

        except Exception:
            return None

    def set(self, address: str, latitude: float, longitude: float, source: str = "nominatim"):
        """Armazena coordenadas no cache"""
        if not address or latitude is None or longitude is None:
            return

        address_hash = self._hash_address(address)
        timestamp = int(time.time())

        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                INSERT OR REPLACE INTO geocoding_cache 
                (address_hash, address, latitude, longitude, source, timestamp, hit_count)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (address_hash, address[:200], latitude, longitude, source, timestamp))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def get_stats(self) -> dict:
        """Retorna estatísticas do cache"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_entries,
                    SUM(hit_count) as total_hits,
                    AVG(hit_count) as avg_hits_per_entry
                FROM geocoding_cache
            """)
            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'total_entries': row[0],
                    'total_hits': row[1],
                    'avg_hits': round(row[2], 2) if row[2] else 0
                }
        except Exception:
            pass

        return {'total_entries': 0, 'total_hits': 0, 'avg_hits': 0}

    def clear_old_entries(self, days: int = 90):
        """Remove entradas antigas do cache"""
        cutoff = int(time.time()) - (days * 86400)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("""
                DELETE FROM geocoding_cache 
                WHERE timestamp < ? AND hit_count < 2
            """, (cutoff,))
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted
        except Exception:
            return 0
