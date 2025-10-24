from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
import uuid
from sqlalchemy.orm import relationship
from app.db.connection import Base

class DoctorSlot(Base):
    __tablename__ = "doctor_slots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    education = Column(String, nullable=False)  
    designation = Column(String, nullable=False)
    location = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    doctor_email = Column(String, nullable=False)
    is_booked = Column(Boolean, default=False)

    
    appointments = relationship('Appointment', back_populates='doctor_slot')

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slot_id = Column(UUID(as_uuid=True), ForeignKey("doctor_slots.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("patients.id"), nullable=False) 
    patient_name = Column(String, nullable=False)
    patient_email = Column(String, nullable=False)
    doctor_email = Column(String, nullable=False)
    status = Column(String, default="confirmed")

    patient = relationship('Patient', back_populates='appointments')
    doctor_slot = relationship('DoctorSlot', back_populates='appointments')
