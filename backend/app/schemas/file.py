from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class FileResponse(BaseModel):
    id: UUID
    name: str
    size: int
    file_url: str
    owner_id: UUID
    folder_id: Optional[UUID] = None
    is_deleted: bool
    starred: bool
    created_at: datetime

    class Config:
        from_attributes = True