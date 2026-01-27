"""
Cache de CEP - Armazena dados de CEP já consultados
Usa banco unificado cache.db
"""
import sqlite3
import time
from pathlib import Path
from typing import Optional, Dict


class CepCache:
    """Cache inteligente de dados de CEP para evitar chamadas repetidas às APIs"""

    def __init__(self):
        self.cache_dir = Path("data/cache")
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.db_path = self.cache_dir / "cache.db"  # ✅ Banco unificado
        self._init_cache_table()

    def _init_cache_table(self):
        """Inicializa tabela de cache de CEP (se não existir)"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cep_cache (
                cep TEXT PRIMARY KEY,
                cidade TEXT,
                uf TEXT,
                bairro TEXT,
                logradouro TEXT,
                complemento TEXT,
                source TEXT,
                timestamp INTEGER,
                hit_count INTEGER DEFAULT 1
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_cep_uf 
            ON cep_cache(uf)
        """)
        conn.commit()
        conn.close()

    def get(self, cep: str) -> Optional[Dict]:
        """Busca dados do CEP no cache"""
        if not cep:
            return None

        clean_cep = ''.join(filter(str.isdigit, cep))

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("""
                SELECT cidade, uf, bairro, logradouro, complemento, source, hit_count
                FROM cep_cache 
                WHERE cep = ?
            """, (clean_cep,))

            row = cursor.fetchone()

            if row:
                cidade, uf, bairro, logradouro, complemento, source, hit_count = row

                # Incrementa contador de hits
                conn.execute("""
                    UPDATE cep_cache 
                    SET hit_count = hit_count + 1 
                    WHERE cep = ?
                """, (clean_cep,))
                conn.commit()
                conn.close()

                return {
                    'cep': clean_cep,
                    'localidade': cidade,
                    'uf': uf,
                    'bairro': bairro,
                    'logradouro': logradouro,
                    'complemento': complemento,
                    'source': f'{source}_cache'
                }

            conn.close()
            return None

        except Exception:
            return None

    def set(self, cep: str, data: Dict):
        """Armazena dados do CEP no cache"""
        if not cep or not data:
            return

        clean_cep = ''.join(filter(str.isdigit, cep))
        timestamp = int(time.time())

        try:
            conn = sqlite3.connect(self.db_path)
            conn.execute("""
                INSERT OR REPLACE INTO cep_cache 
                (cep, cidade, uf, bairro, logradouro, complemento, source, timestamp, hit_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                clean_cep,
                data.get('localidade', ''),
                data.get('uf', ''),
                data.get('bairro', ''),
                data.get('logradouro', ''),
                data.get('complemento', ''),
                data.get('source', 'unknown'),
                timestamp
            ))
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
                FROM cep_cache
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

    def clear_old_entries(self, days: int = 180):
        """Remove entradas antigas do cache"""
        cutoff = int(time.time()) - (days * 86400)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("""
                DELETE FROM cep_cache 
                WHERE timestamp < ? AND hit_count < 2
            """, (cutoff,))
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            return deleted
        except Exception:
            return 0
