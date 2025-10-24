from pydantic import BaseModel, EmailStr, UUID4
from typing import Optional

class DoctorBase(BaseModel):
    name: str
    email: EmailStr
    designation: str
    education: str
    location: Optional[str] = None

class DoctorCreate(DoctorBase):
    pass

class DoctorRead(DoctorBase):
    id: UUID4

    class Config:
        from_attributes = True