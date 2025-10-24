from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.connection import Base

class Doctor(Base):
    __tablename__ = 'doctors'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    designation = Column(String, nullable=False)
    education = Column(String, nullable=False)
    location = Column(String, nullable=True)