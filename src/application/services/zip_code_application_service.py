from typing import Optional
import logging

from src.infrastructure.repositories.zip_code_repository import ZipCodeRepository

logger = logging.getLogger(__name__)


class ZipCodeApplicationService:
    KEY = 'reference_cep'

    def __init__(self):
        self.repo = ZipCodeRepository()

    def get_reference_cep(self) -> Optional[dict]:
        """Always attempt to read the reference CEP from TB_CEP_CONFIG.

        If no row exists, attempt to seed the table with the CEP defined in
        application.yaml at 'geolocation.reference_cep'. When seeding, call the
        AddressEnrichmentService (ViaCEP) to obtain the full address info; if
        the CEP is invalid the method will raise ValueError.
        """
        try:
            res = self.repo.get_reference()
        except Exception as e:
            logger.warning("[ZipCodeService] failed to read TB_CEP_CONFIG: %s", e)
            res = None

        if res:
            return res

        # No record in DB -> try to seed from YAML
        try:
            from src.infrastructure.config.config_manager import ConfigManager
            cfg = ConfigManager()
            yaml_cep = cfg.get('geolocation.reference_cep', None)
            if not yaml_cep:
                logger.debug('[ZipCodeService] No geolocation.reference_cep in YAML to seed TB_CEP_CONFIG')
                return None

            # Normalize CEP string
            import re
            cep_clean = re.sub(r'\D', '', yaml_cep)
            if len(cep_clean) != 8:
                # Invalid format in YAML -> raise so caller knows
                raise ValueError(f"CEP de referência no YAML com formato inválido: {yaml_cep}")
            formatted = f"{cep_clean[:5]}-{cep_clean[5:]}"

            # IMPORTANT: use AddressEnrichmentService to fetch full CEP data BEFORE persisting
            try:
                from src.domain.services.address_enrichment_service import AddressEnrichmentService
                enrichment = AddressEnrichmentService()
                cep_data = enrichment._fetch_cep_data(formatted)
            except Exception as e:
                logger.warning('[ZipCodeService] Error calling AddressEnrichmentService: %s', e)
                raise

            # If CEP not found or invalid, raise
            if not cep_data or not isinstance(cep_data, dict) or not cep_data.get('cep'):
                raise ValueError(f"CEP de referência inválido ou não encontrado: {yaml_cep}")

            cidade = cep_data.get('localidade', '') or ''
            estado = cep_data.get('uf', '') or ''
            logradouro = cep_data.get('logradouro', '') or ''

            # Seed using full data
            try:
                ok = self.repo.upsert_reference(formatted, cidade, estado, logradouro)
                if not ok:
                    raise RuntimeError('Falha ao gravar TB_CEP_CONFIG durante o seed')
                return self.repo.get_reference()
            except Exception as e:
                logger.warning('[ZipCodeService] Error seeding TB_CEP_CONFIG: %s', e)
                raise

        except Exception:
            # Propagate exception to caller (caller may handle/log as needed)
            raise

    def set_reference_cep(self, cep: str) -> bool:
        # validate input
        if not cep or not isinstance(cep, str):
            return False
        import re
        cep_clean = re.sub(r'\D', '', cep)
        if len(cep_clean) != 8:
            return False

        # Use domain service to fetch CEP data (ViaCEP) and then upsert
        try:
            from src.domain.services.address_enrichment_service import AddressEnrichmentService
            svc = AddressEnrichmentService()
            logger.debug("[ZipCodeService] Looking up CEP via AddressEnrichmentService: %s", cep)
            cep_data = svc._fetch_cep_data(cep)
            logger.debug("[ZipCodeService] ViaCEP result: %s", cep_data)
            if not cep_data:
                return False
            cidade = cep_data.get('localidade', '')
            estado = cep_data.get('uf', '')
            logradouro = cep_data.get('logradouro', '')
            formatted = f"{cep_clean[:5]}-{cep_clean[5:]}"
            ok = self.repo.upsert_reference(formatted, cidade, estado, logradouro)
            logger.debug("[ZipCodeService] upsert_reference returned: %s", ok)
            return ok
        except Exception as e:
            logger.warning("[AVISO] Falha ao consultar ViaCEP/validar CEP: %s", e)
            raise

    def invalidate_cache(self):
        """No-op: caching removed. Kept for compatibility."""
        return None

    def ensure_table_and_seed(self) -> bool:
        """Ensure TB_CEP_CONFIG exists and, if empty, seed from YAML (single-row).

        This method will raise exceptions coming from `get_reference_cep()` (e.g. invalid CEP)
        so callers can handle/report them appropriately during startup.
        """
        ok_table = self.repo.ensure_table_exists()
        if not ok_table:
            logger.warning('[AVISO] Não foi possível garantir existência de TB_CEP_CONFIG')
            return False

        existing = self.repo.get_reference()
        if existing:
            return True

        # seed from YAML (this may raise if invalid)
        seeded_row = self.get_reference_cep()
        return bool(seeded_row)
