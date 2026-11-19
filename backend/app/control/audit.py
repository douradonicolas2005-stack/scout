"""Audit event interfaces (skeleton). Persistence wired in Subetapa B."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class AuditEventDraft:
    action: str
    target_type: str
    target_id: Optional[str] = None
    actor_type: str = "system"
    actor_id: Optional[str] = None
    severity: str = "info"
    details: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
