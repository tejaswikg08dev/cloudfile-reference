"""Pydantic schemas for the notification service."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class NotifyRequest(BaseModel):
    recipient: EmailStr
    subject: str = Field(min_length=1, max_length=512)
    message: str = Field(min_length=1, max_length=5000)
    channel: str = Field(default="email", pattern="^(email|sms|push)$")


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    recipient: EmailStr
    subject: str
    message: str
    channel: str
    status: str
    created_at: datetime
