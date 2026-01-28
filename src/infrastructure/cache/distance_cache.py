"""
Cache de Distâncias - Armazena distâncias já calculadas entre pares de localizações
Usa banco unificado pythonsearchcache.db
"""
import sqlite3
import time
from pathlib import Path
from typing import Optional


class DistanceCache:
    """Cache de distâncias entre pares de coordenadas para evitar recálculos"""

    def __init__(self):
        self.cache_dir = Path("data/cache")
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.db_path = self.cache_dir / "pythonsearchcache.db"  # ✅ Banco unificado
        self._conn = None  # Conexão persistente
        # Tabela criada por scripts/database/create_cache_db.py

    def _get_connection(self):
        """Retorna conexão persistente (singleton)"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging para performance
            self._conn.execute("PRAGMA synchronous=NORMAL")  # Performance otimizada
        return self._conn

    def __del__(self):
        """Fecha conexão ao destruir objeto"""
        if self._conn:
            try:
                self._conn.close()
            except:
                pass


    def _make_key(self, origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float) -> tuple:
        """Cria chave única para o par de coordenadas (arredondado para 4 casas decimais)"""
        return (
            round(origin_lat, 4),
            round(origin_lon, 4),
            round(dest_lat, 4),
            round(dest_lon, 4)
        )

    def get(self, origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float) -> Optional[float]:
        """Busca distância no cache"""
        if not all([origin_lat, origin_lon, dest_lat, dest_lon]):
            return None

        key = self._make_key(origin_lat, origin_lon, dest_lat, dest_lon)

        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT distance_km
                FROM distance_cache 
                WHERE origin_lat = ? AND origin_lon = ? 
                AND dest_lat = ? AND dest_lon = ?
            """, key)

            row = cursor.fetchone()

            if row:
                distance_km = row[0]

                # Incrementa contador de hits
                conn.execute("""
                    UPDATE distance_cache 
                    SET hit_count = hit_count + 1 
                    WHERE origin_lat = ? AND origin_lon = ? 
                    AND dest_lat = ? AND dest_lon = ?
                """, key)
                conn.commit()
                return distance_km

            return None

        except Exception:
            return None

    def set(self, origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float, distance_km: float):
        """Armazena distância no cache"""
        if not all([origin_lat, origin_lon, dest_lat, dest_lon]) or distance_km is None:
            return

        key = self._make_key(origin_lat, origin_lon, dest_lat, dest_lon)
        timestamp = int(time.time())

        try:
            conn = self._get_connection()
            conn.execute("""
                INSERT OR REPLACE INTO distance_cache 
                (origin_lat, origin_lon, dest_lat, dest_lon, distance_km, timestamp, hit_count)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (*key, distance_km, timestamp))
            conn.commit()
        except Exception:
            pass

    def get_stats(self) -> dict:
        """Retorna estatísticas do cache"""
        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_entries,
                    SUM(hit_count) as total_hits,
                    AVG(hit_count) as avg_hits_per_entry,
                    AVG(distance_km) as avg_distance_km
                FROM distance_cache
            """)
            row = cursor.fetchone()

            if row:
                return {
                    'total_entries': row[0],
                    'total_hits': row[1],
                    'avg_hits': round(row[2], 2) if row[2] else 0,
                    'avg_distance': round(row[3], 2) if row[3] else 0
                }
        except Exception:
            pass

        return {'total_entries': 0, 'total_hits': 0, 'avg_hits': 0, 'avg_distance': 0}

    def clear_old_entries(self, days: int = 365):
        """Remove entradas antigas do cache (padrão: 1 ano)"""
        cutoff = int(time.time()) - (days * 86400)

        try:
            conn = self._get_connection()
            cursor = conn.execute("""
                DELETE FROM distance_cache 
                WHERE timestamp < ? AND hit_count < 2
            """, (cutoff,))
            deleted = cursor.rowcount
            conn.commit()
            return deleted
        except Exception:
            return 0
