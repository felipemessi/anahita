"""Unit tests for the get_storage_service() factory."""

import pytest

from app import config
from app.storage import get_storage_service
from app.storage.local import LocalStorageService


def test_factory_returns_local_service(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """get_storage_service() returns LocalStorageService when storage_type='local'."""
    monkeypatch.setattr(config.settings, "storage_type", "local")
    monkeypatch.setattr(config.settings, "storage_local_path", str(tmp_path))

    svc = get_storage_service()

    assert isinstance(svc, LocalStorageService)


def test_factory_raises_for_unknown_type(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """get_storage_service() raises ValueError for unrecognised storage_type values."""
    monkeypatch.setattr(config.settings, "storage_type", "s3_not_yet")

    with pytest.raises(ValueError, match="Unknown storage_type"):
        get_storage_service()
