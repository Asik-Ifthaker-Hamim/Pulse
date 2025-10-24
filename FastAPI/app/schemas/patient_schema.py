from pydantic import BaseModel, EmailStr, UUID4
from typing import Optional

class PatientBase(BaseModel):
    name: str
    email: EmailStr
    contact_number: str
    address: Optional[str] = None
    date_of_birth: Optional[str] = None

class PatientCreate(PatientBase):
    pass

class PatientRead(PatientBase):
    id: UUID4

    class Config:
        from_attributes = True