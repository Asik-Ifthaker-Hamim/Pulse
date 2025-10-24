from sqlalchemy import Column, String, Text
from app.db.connection import Base

class SOAPPrescription(Base):
    __tablename__ = "soap_prescriptions"

    id = Column(String, primary_key=True, index=True)  
    consultation_id = Column(String, index=True)
    report = Column(Text)  
