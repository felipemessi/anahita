"""Unit tests for LocalStorageService — no database, no Docker."""

from pathlib import Path

import pytest

from app.storage.local import LocalStorageService


@pytest.fixture()
def svc(tmp_path: Path) -> LocalStorageService:
    """Return a LocalStorageService rooted at a temporary directory."""
    return LocalStorageService(str(tmp_path))


def test_upload_writes_bytes(svc: LocalStorageService, tmp_path: Path) -> None:
    """upload() persists data and returns the original key."""
    key = "handouts/campaign_1/map.png"
    data = b"fake image data"

    result = svc.upload(key, data, "image/png")

    assert result == key
    assert (tmp_path / key).read_bytes() == data


def test_upload_creates_parent_directories(svc: LocalStorageService, tmp_path: Path) -> None:
    """upload() creates intermediate directories automatically."""
    key = "tokens/campaign_abc/dragon.png"
    svc.upload(key, b"\x89PNG", "image/png")
    assert (tmp_path / key).exists()


def test_get_url_returns_files_prefix(svc: LocalStorageService) -> None:
    """get_url() returns a /files/ URL that Nginx will serve directly."""
    url = svc.get_url("handouts/campaign_1/map.png")
    assert url == "/files/handouts/campaign_1/map.png"


def test_delete_removes_existing_file(svc: LocalStorageService, tmp_path: Path) -> None:
    """delete() removes the file from disk."""
    key = "tokens/campaign_1/goblin.png"
    svc.upload(key, b"data", "image/png")
    assert (tmp_path / key).exists()

    svc.delete(key)

    assert not (tmp_path / key).exists()


def test_delete_nonexistent_file_does_not_raise(svc: LocalStorageService) -> None:
    """delete() is idempotent — no error when the file is missing."""
    svc.delete("nonexistent/file.png")
