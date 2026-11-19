from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    actor_type: str
    actor_id: Optional[str] = None
    action: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    severity: str
    details_json: Optional[Dict[str, Any]] = None
    ip_or_origin: Optional[str] = None
    created_at: datetime


class AuditEventListResponse(BaseModel):
    items: List[AuditEventResponse]
