from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ConnectorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    key: str
    name: str
    version: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None
    config_schema: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    updated_at: datetime


class ConnectorListResponse(BaseModel):
    items: List[ConnectorResponse]


class SourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    resource_locator: str = Field(..., min_length=1)
    connection_type: str = Field(..., min_length=1, max_length=100)
    auth_method: Optional[str] = Field(default=None, max_length=100)
    auth_credential_ref: Optional[str] = Field(default=None, max_length=255)
    frequency: Optional[str] = Field(default=None, max_length=100)
    status: str = Field(default="inactive", max_length=50)
    config_json: Optional[Dict[str, Any]] = None
    permissions_json: Optional[Dict[str, Any]] = None
    terms_conditions: Optional[str] = None
    is_active: bool = False
    created_by: Optional[str] = Field(default=None, max_length=100)


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    category: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = None
    resource_locator: Optional[str] = Field(default=None, min_length=1)
    connection_type: Optional[str] = Field(default=None, min_length=1, max_length=100)
    auth_method: Optional[str] = Field(default=None, max_length=100)
    auth_credential_ref: Optional[str] = Field(default=None, max_length=255)
    frequency: Optional[str] = Field(default=None, max_length=100)
    status: Optional[str] = Field(default=None, max_length=50)
    config_json: Optional[Dict[str, Any]] = None
    permissions_json: Optional[Dict[str, Any]] = None
    terms_conditions: Optional[str] = None
    is_active: Optional[bool] = None


class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    resource_locator: str
    connection_type: str
    auth_method: Optional[str] = None
    auth_credential_ref: Optional[str] = None
    frequency: Optional[str] = None
    status: str
    last_collected_at: Optional[datetime] = None
    next_collect_at: Optional[datetime] = None
    config_json: Optional[Dict[str, Any]] = None
    permissions_json: Optional[Dict[str, Any]] = None
    terms_conditions: Optional[str] = None
    is_active: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SourceListResponse(BaseModel):
    items: List[SourceResponse]


class SourceTestConnectionResponse(BaseModel):
    source_id: str
    connector_key: str
    ok: bool
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tested_at: datetime
