from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Optional


ReservationState = Literal["PENDING", "CONFIRMED", "CANCELLED", "FINISHED"]


class ReservationCreate(BaseModel):
    start: datetime
    end: datetime
    user_id: int
    price_list_id: int
    courts_id: int
    state: ReservationState = "PENDING"


class ReservationUpdate(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    user_id: Optional[int] = None
    price_list_id: Optional[int] = None
    courts_id: Optional[int] = None
    state: Optional[ReservationState] = None
    price_total: Optional[float] = Field(default=None, gt=0)


class Reservation(ReservationCreate):
    reservation_id: int
    price_total: float
    created_at: datetime

    class Config:
        from_attributes = True
