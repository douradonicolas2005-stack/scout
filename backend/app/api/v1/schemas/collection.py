from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CollectionJobCreate(BaseModel):
    source_id: str = Field(..., min_length=1)
    trigger: str = Field(default="manual", max_length=50)
    requested_by: Optional[str] = Field(default=None, max_length=100)
    scheduled_for: Optional[datetime] = None
    max_attempts: int = Field(default=3, ge=1, le=5)
    execute_now: bool = True


class CollectionJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: str
    trigger: str
    status: str
    priority: int
    scheduled_for: Optional[datetime] = None
    attempt: int
    max_attempts: int
    requested_by: Optional[str] = None
    cancel_requested: bool
    error_summary: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class CollectionJobListResponse(BaseModel):
    items: List[CollectionJobResponse]


class CollectionRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    source_id: str
    run_number: int
    status: str
    items_found: int
    items_stored: int
    items_deduplicated: int
    items_invalid: int
    bytes_downloaded: int
    error_message: Optional[str] = None
    metrics_json: Optional[Dict[str, Any]] = None
    started_at: datetime
    finished_at: Optional[datetime] = None


class CollectionRunListResponse(BaseModel):
    items: List[CollectionRunResponse]


class ProcessingEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: Optional[str] = None
    run_id: Optional[str] = None
    stage: str
    status: str
    message: Optional[str] = None
    payload_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    duration_ms: Optional[int] = None


class ProcessingEventListResponse(BaseModel):
    items: List[ProcessingEventResponse]


class JobExecutionResponse(BaseModel):
    job: CollectionJobResponse
    run: Optional[CollectionRunResponse] = None
