from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ModuleStatus(BaseModel):
    key: str
    label: str
    path: str
    status: Literal["placeholder", "planned", "in_development", "implemented"] = "placeholder"
    implemented: bool = False


class SystemInfoResponse(BaseModel):
    app_name: str
    version: str
    phase: str
    environment: str
    api_version: str = "v1"
    docs_url: str = "/docs"
    openapi_url: str = "/openapi.json"
    database: Literal["sqlite"] = "sqlite"
    ollama: Dict[str, Optional[str]] = Field(default_factory=dict)
    scheduler: Dict[str, object] = Field(default_factory=dict)
    modules: List[ModuleStatus] = Field(default_factory=list)
    timestamp: datetime


class DbTableStat(BaseModel):
    name: str
    row_count: int


class DbStatusResponse(BaseModel):
    connected: bool
    dialect: str
    database_url: str
    table_count: int
    tables: List[DbTableStat] = Field(default_factory=list)
    alembic_revision: Optional[str] = None
    alembic_revisions: List[str] = Field(default_factory=list)
    foreign_keys: Optional[int] = None
    journal_mode: Optional[str] = None
    busy_timeout: Optional[int] = None
    error: Optional[str] = None
    timestamp: datetime
