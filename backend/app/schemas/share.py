from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, Literal

class ShareCreate(BaseModel):
    file_id: UUID
    shared_with_email: str
    role: Literal["viewer", "editor"]

class ShareResponse(BaseModel):
    id: UUID
    file_id: UUID
    shared_with_user_id: UUID
    role: str

    class Config:
        from_attributes = True

class LinkShareCreate(BaseModel):
    file_id: UUID
    expires_in_hours: Optional[int] = None
    password: Optional[str] = None

class LinkShareResponse(BaseModel):
    id: UUID
    file_id: UUID
    token: str
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True