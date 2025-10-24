from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import uuid
from app.db.connection import Base

class Patient(Base):
    __tablename__ = 'patients'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4) 
    name = Column(String, nullable=False)  
    email = Column(String, nullable=False, unique=True)  
    contact_number = Column(String, nullable=False)  
    address = Column(String)  
    date_of_birth = Column(String)  

    
    appointments = relationship('Appointment', back_populates='patient')
