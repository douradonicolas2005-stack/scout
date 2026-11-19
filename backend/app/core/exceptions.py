from __future__ import annotations


class ScoutError(Exception):
    """Base application exception."""


class ConfigurationError(ScoutError):
    """Raised when required local configuration is invalid or missing."""


class NotFoundError(ScoutError):
    """Raised when a requested resource does not exist."""


class ExternalServiceUnavailableError(ScoutError):
    """Raised when a local/external dependency (e.g. Ollama) is unavailable."""
