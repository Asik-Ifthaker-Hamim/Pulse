from pydantic import BaseModel, UUID4
from typing import Optional
from datetime import datetime

class SlotBase(BaseModel):
    doctor_id: str 
    name: str
    education: str
    designation: str
    location: str
    start_time: datetime
    end_time: datetime
    doctor_email: str
    is_booked: bool

class SlotRead(SlotBase):
    id: UUID4

    class Config:
        from_attributes = True 
