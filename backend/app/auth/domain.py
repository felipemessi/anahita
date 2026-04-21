"""Auth domain enums and value types."""

from enum import StrEnum


class ProviderType(StrEnum):
    """Supported authentication provider types."""

    local = "local"
    discord = "discord"
    google = "google"
