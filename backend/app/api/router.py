from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    audit,
    collection,
    dossiers,
    dossiers_research,
    health,
    ingestion,
    system,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router, tags=["system"])
api_router.include_router(system.router, tags=["system"])
api_router.include_router(ingestion.router, tags=["ingestion"])
api_router.include_router(collection.router, tags=["ingestion"])
api_router.include_router(audit.router, tags=["system"])
api_router.include_router(dossiers.router)
api_router.include_router(dossiers_research.router)
