from sqlalchemy.orm import Session
from app.models.soap_prescription_model import SOAPPrescription
import uuid

def save_soap_prescription(db: Session, consultation_id: str, report: str) -> SOAPPrescription:
    new_id = str(uuid.uuid4())
    soap_entry = SOAPPrescription(id=new_id, consultation_id=consultation_id, report=report)
    db.add(soap_entry)
    db.commit()
    db.refresh(soap_entry)
    return soap_entry