from typing import Optional
from .access_repository import AccessRepository


class ZipCodeRepository:
    """Repository to manage TB_CEP_CONFIG rows (single-row configuration for reference CEP)."""

    def __init__(self):
        self._repo = AccessRepository()

    def get_reference(self) -> Optional[dict]:
        """Return the reference CEP row as dict or None if not present"""
        import time
        max_attempts = 4
        delay = 0.2
        last_exc = None
        for attempt in range(1, max_attempts + 1):
            try:
                conn = self._repo._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT CEP, CIDADE, ESTADO, LOGRADOURO, RAIO_KM, DATA_ATUALIZACAO FROM TB_CEP_CONFIG ORDER BY ID_CEP_CONFIG DESC")
                row = cursor.fetchone()
                cursor.close()
                if not row:
                    return None
                return {
                    'cep': row[0],
                    'cidade': row[1],
                    'estado': row[2],
                    'logradouro': row[3],
                    'raio_km': row[4],
                    'updated_at': row[5]
                }
            except Exception as e:
                last_exc = e
                msg = str(e)
                # Detect common Access locked/file-in-use error strings and retry briefly
                if 'ficheiro já em utilização' in msg or 'file already in use' in msg or '(-1024)' in msg or 'HY000' in msg:
                    if attempt < max_attempts:
                        time.sleep(delay)
                        delay *= 2
                        continue
                # For other errors or exhausted attempts, log and return None
                print(f"[AVISO] Falha ao ler TB_CEP_CONFIG (attempt {attempt}/{max_attempts}): {e}")
                return None
        # If somehow loop exits, return None
        print(f"[AVISO] Falha ao ler TB_CEP_CONFIG após {max_attempts} tentativas: {last_exc}")
        return None

    def upsert_reference(self, cep: str, cidade: str, estado: str, logradouro: str) -> bool:
        """Insert or update the single reference CEP row."""
        import time
        max_attempts = 4
        delay = 0.2
        last_exc = None
        print(f"[DEBUG][ZipCodeRepository] upsert_reference called with cep={cep} cidade={cidade} estado={estado} logradouro={logradouro}")
        for attempt in range(1, max_attempts + 1):
            try:
                conn = self._repo._get_connection()
                cursor = conn.cursor()
                # If any row exists, update the latest (or we can delete/insert)
                cursor.execute("SELECT COUNT(*) FROM TB_CEP_CONFIG")
                r = cursor.fetchone()
                exists = (r[0] if r else 0) > 0
                print(f"[DEBUG][ZipCodeRepository] TB_CEP_CONFIG exists? {exists}")
                # If a raio_km value has been passed via kwargs, include it in upsert
                # keep function signature backwards compatible by reading optional attribute on self
                raio_km = getattr(self, '_last_raio_km', None)
                if exists:
                    if raio_km is not None:
                        cursor.execute("UPDATE TB_CEP_CONFIG SET CEP = ?, CIDADE = ?, ESTADO = ?, LOGRADOURO = ?, RAIO_KM = ?, DATA_ATUALIZACAO = Date()", (cep, cidade, estado, logradouro, int(raio_km)))
                    else:
                        cursor.execute("UPDATE TB_CEP_CONFIG SET CEP = ?, CIDADE = ?, ESTADO = ?, LOGRADOURO = ?, DATA_ATUALIZACAO = Date()", (cep, cidade, estado, logradouro))
                else:
                    if raio_km is not None:
                        cursor.execute("INSERT INTO TB_CEP_CONFIG (CEP, CIDADE, ESTADO, LOGRADOURO, RAIO_KM, DATA_ATUALIZACAO) VALUES (?, ?, ?, ?, ?, Date())", (cep, cidade, estado, logradouro, int(raio_km)))
                    else:
                        cursor.execute("INSERT INTO TB_CEP_CONFIG (CEP, CIDADE, ESTADO, LOGRADOURO, DATA_ATUALIZACAO) VALUES (?, ?, ?, ?, Date())", (cep, cidade, estado, logradouro))
                conn.commit()
                cursor.close()
                print(f"[DEBUG][ZipCodeRepository] upsert_reference successful for cep={cep}")
                return True
            except Exception as e:
                last_exc = e
                msg = str(e)
                if 'ficheiro já em utilização' in msg or 'file already in use' in msg or '(-1024)' in msg or 'HY000' in msg:
                    if attempt < max_attempts:
                        time.sleep(delay)
                        delay *= 2
                        continue
                print(f"[AVISO] Falha ao gravar TB_CEP_CONFIG (attempt {attempt}/{max_attempts}): {e}")
                return False
        print(f"[AVISO] Falha ao gravar TB_CEP_CONFIG após {max_attempts} tentativas: {last_exc}")
        return False

    def ensure_table_exists(self) -> bool:
        """Ensure the TB_CEP_CONFIG table exists in the Access DB. Returns True if table exists or was created."""
        import time
        max_attempts = 3
        delay = 0.2
        last_exc = None
        for attempt in range(1, max_attempts + 1):
            try:
                conn = self._repo._get_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute("SELECT COUNT(*) FROM TB_CEP_CONFIG")
                    cursor.close()
                    return True
                except Exception:
                    # Try to create the table
                    try:
                        create_sql = (
                            "CREATE TABLE TB_CEP_CONFIG ("
                            "ID_CEP_CONFIG COUNTER PRIMARY KEY, "
                            "CEP TEXT(10), CIDADE TEXT(100), ESTADO TEXT(2), LOGRADOURO TEXT(255), RAIO_KM INTEGER, DATA_ATUALIZACAO DATE)"
                        )
                        cursor.execute(create_sql)
                        conn.commit()
                        try:
                            cursor.close()
                        except Exception:
                            pass
                        print('[INFO] TB_CEP_CONFIG criada no banco (via repository)')
                        return True
                    except Exception as e:
                        last_exc = e
                        msg = str(e)
                        if 'ficheiro já em utilização' in msg or 'file already in use' in msg or '(-1024)' in msg or 'HY000' in msg:
                            if attempt < max_attempts:
                                time.sleep(delay)
                                delay *= 2
                                continue
                        print(f"[AVISO] Falha ao criar TB_CEP_CONFIG no repository: {e}")
                        try:
                            cursor.close()
                        except Exception:
                            pass
                        return False
            except Exception as e:
                last_exc = e
                msg = str(e)
                if 'ficheiro já em utilização' in msg or 'file already in use' in msg or '(-1024)' in msg or 'HY000' in msg:
                    if attempt < max_attempts:
                        time.sleep(delay)
                        delay *= 2
                        continue
                print(f"[AVISO] Falha ao garantir TB_CEP_CONFIG: {e}")
                return False
        print(f"[AVISO] Falha ao garantir TB_CEP_CONFIG após {max_attempts} tentativas: {last_exc}")
        return False
