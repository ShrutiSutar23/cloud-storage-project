from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base

class LinkShare(Base):
    __tablename__ = "link_shares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("files.id"))
    token = Column(String, unique=True)
    expires_at = Column(DateTime, nullable=True)
    password = Column(String, nullable=True)