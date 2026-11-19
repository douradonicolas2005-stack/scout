from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.ingestion.scheduler import get_scheduler, reset_scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan (Foundation F: scheduler with DB-canonical rehydration)."""
    setup_logging()
    settings.ensure_storage_dirs()
    # Schema is managed by Alembic migrations (Subetapa B+).
    scheduler = get_scheduler(
        enabled=settings.scheduler_enabled,
        max_concurrent_jobs=settings.scheduler_max_concurrent_jobs,
    )
    scheduler.start()
    logger.info(
        "SCOUT API starting (phase=foundation-g, host=%s, port=%s)",
        settings.host,
        settings.port,
    )
    try:
        yield
    finally:
        scheduler.shutdown()
        reset_scheduler()
        logger.info("SCOUT API stopping")


app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
