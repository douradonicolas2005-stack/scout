from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.api.v1.schemas.common import HealthResponse
from app.core.config import settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Lightweight liveness/identity endpoint (loopback)."""
    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        phase="foundation-g",
        timestamp=datetime.now(timezone.utc),
    )
