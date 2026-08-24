from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.core.database import Base

class Folder(Base):
    __tablename__ = "folders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    parent_folder_id = Column(UUID(as_uuid=True), ForeignKey("folders.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)