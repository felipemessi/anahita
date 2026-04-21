"""Abstract base class for the storage service."""

from abc import ABC, abstractmethod


class StorageService(ABC):
    """Interface for file storage operations."""

    @abstractmethod
    def upload(self, key: str, data: bytes, content_type: str) -> str:
        """Persist *data* under *key* and return the key."""

    @abstractmethod
    def get_url(self, key: str) -> str:
        """Resolve *key* to a publicly accessible URL."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Remove the file identified by *key*."""
