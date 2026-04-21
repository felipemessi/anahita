"""Local filesystem implementation of StorageService."""

from pathlib import Path

from app.storage.base import StorageService


class LocalStorageService(StorageService):
    """Stores files on the local filesystem under *base_path*."""

    def __init__(self, base_path: str) -> None:
        """Initialise with the root directory for uploads."""
        self._base = Path(base_path)

    def upload(self, key: str, data: bytes, content_type: str) -> str:
        """Write *data* to ``<base_path>/<key>`` and return the key."""
        dest = self._base / key
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return key

    def get_url(self, key: str) -> str:
        """Return the Nginx-served URL for *key*."""
        return f"/files/{key}"

    def delete(self, key: str) -> None:
        """Remove ``<base_path>/<key>`` if it exists."""
        path = self._base / key
        if path.exists():
            path.unlink()
