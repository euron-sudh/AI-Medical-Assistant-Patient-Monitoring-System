"""Notification request/response schemas — Pydantic validation."""

from datetime import datetime

from pydantic import BaseModel, Field


class CreateNotificationRequest(BaseModel):
    """Schema for creating a new notification."""

    user_id: str
    type: str = Field(max_length=50)
    title: str = Field(max_length=255)
    message: str
    data: dict | None = None
    channel: str = Field(default="in_app", pattern="^(in_app|email|sms|push)$")


class NotificationResponse(BaseModel):
    """Schema for notification in responses."""

    id: str
    user_id: str
    type: str
    title: str
    message: str
    data: dict | None = None
    read: bool
    read_at: datetime | None = None
    channel: str
    sent_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationListParams(BaseModel):
    """Schema for notification list query parameters."""

    unread_only: bool = False
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class AuditLogResponse(BaseModel):
    """Schema for audit log in responses."""

    id: str
    user_id: str
    action: str
    resource_type: str
    resource_id: str | None = None
    patient_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    request_method: str | None = None
    request_path: str | None = None
    status_code: int | None = None
    details: dict | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogQueryParams(BaseModel):
    """Schema for audit log query parameters."""

    user_id: str | None = None
    patient_id: str | None = None
    action: str | None = None
    resource_type: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
