from typing import Optional

from src.infrastructure.repositories.zip_code_repository import ZipCodeRepository

# Module-level global cache (per-process) - shared by all ZipCodeService instances
_GLOBAL_ZIP_CACHE: Optional[dict] = None


class ZipCodeService:
    KEY = 'reference_cep'

    def __init__(self):
        self.repo = ZipCodeRepository()

    def get_reference_cep(self) -> Optional[dict]:
        """Returns dict with cep, cidade, estado, logradouro or None.

        Uses a module-level cache `_GLOBAL_ZIP_CACHE` to avoid repeated DB reads
        across multiple instances in the same process.
        """
        global _GLOBAL_ZIP_CACHE
        if _GLOBAL_ZIP_CACHE is not None:
            print("[DEBUG][ZipCodeService] get_reference_cep returned from global cache")
            return _GLOBAL_ZIP_CACHE

        print("[DEBUG][ZipCodeService] get_reference_cep called (DB read)")
        res = self.repo.get_reference()
        print(f"[DEBUG][ZipCodeService] get_reference_cep result: {res}")
        _GLOBAL_ZIP_CACHE = res
        return res

    def set_reference_cep(self, cep: str) -> bool:
        # validate input
        if not cep or not isinstance(cep, str):
            return False
        import re
        cep_clean = re.sub(r'\D', '', cep)
        if len(cep_clean) != 8:
            return False

        # Use domain service to fetch CEP data (ViaCEP)
        try:
            from src.domain.services.address_enrichment_service import AddressEnrichmentService
            svc = AddressEnrichmentService()
            print(f"[DEBUG][ZipCodeService] Looking up CEP via AddressEnrichmentService: {cep}")
            cep_data = svc._fetch_cep_data(cep)
            print(f"[DEBUG][ZipCodeService] ViaCEP result: {cep_data}")
            if not cep_data:
                return False
            cidade = cep_data.get('localidade', '')
            estado = cep_data.get('uf', '')
            logradouro = cep_data.get('logradouro', '')
            # format CEP as 12345-678
            formatted = f"{cep_clean[:5]}-{cep_clean[5:]}"
            ok = self.repo.upsert_reference(formatted, cidade, estado, logradouro)
            print(f"[DEBUG][ZipCodeService] upsert_reference returned: {ok}")
            if ok:
                # update cache to reflect new DB state (use minimal shape)
                from datetime import datetime
                _GLOBAL_ZIP_CACHE = {
                    'cep': formatted,
                    'cidade': cidade,
                    'estado': estado,
                    'logradouro': logradouro,
                    'updated_at': datetime.now()
                }
            return ok
        except Exception as e:
            print(f"[AVISO] Falha ao consultar ViaCEP/validar CEP: {e}")
            return False

    def invalidate_cache(self):
        """Invalidate the in-memory cache (useful if DB changed externally)."""
        global _GLOBAL_ZIP_CACHE
        _GLOBAL_ZIP_CACHE = None

    def ensure_table_and_seed(self) -> bool:
        """Ensure TB_CEP_CONFIG exists and has a seed value (from YAML) if missing."""
        try:
            # Ensure table exists
            ok_table = self.repo.ensure_table_exists()
            if not ok_table:
                print('[AVISO] Não foi possível garantir existência de TB_CEP_CONFIG')
                return False

            # Check if a row exists
            existing = self.get_reference_cep()
            if existing:
                print('[DEBUG][ZipCodeService] TB_CEP_CONFIG já contém um registro, sem seed necessário')
                return True

            # Seed from YAML config
            try:
                from src.infrastructure.config.config_manager import ConfigManager
                cfg = ConfigManager()
                # For seeding we must read the raw YAML value (no DB resolution)
                yaml_cep = cfg.get('geolocation.reference_cep', None)
            except Exception:
                yaml_cep = None

            if yaml_cep:
                print(f"[INFO] Seedando TB_CEP_CONFIG a partir do YAML: {yaml_cep}")
                return self.set_reference_cep(yaml_cep)

            print('[AVISO] Nenhum CEP para seed encontrado no YAML')
            return False
        except Exception as e:
            print(f"[AVISO] Erro em ensure_table_and_seed: {e}")
            return False
