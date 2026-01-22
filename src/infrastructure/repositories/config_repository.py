from typing import Optional
# Deprecated shim - use src.infrastructure.repositories.zip_code_repository.ZipCodeRepository
from src.infrastructure.repositories.zip_code_repository import ZipCodeRepository as ZipCodeRepository


class ConfigRepository(ZipCodeRepository):
    """Deprecated alias for ZipCodeRepository. Kept for backward compatibility."""
    pass
