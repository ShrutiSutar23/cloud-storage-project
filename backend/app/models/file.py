from sqlalchemy import Column, String, BigInteger, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.core.database import Base
from app.models.folder import Folder

class File(Base):
    __tablename__ = "files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    size = Column(BigInteger)
    file_url = Column(String)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    folder_id = Column(UUID(as_uuid=True), ForeignKey("folders.id"), nullable=True)
    is_deleted = Column(Boolean, default=False)
    starred = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)