"""Storage service factory."""

from app.config import settings
from app.storage.base import StorageService
from app.storage.local import LocalStorageService


def get_storage_service() -> StorageService:
    """Return the configured StorageService implementation."""
    if settings.storage_type == "local":
        return LocalStorageService(settings.storage_local_path)
    raise ValueError(f"Unknown storage_type: {settings.storage_type!r}")
