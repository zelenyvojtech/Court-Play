from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TimeBlockCreate(BaseModel):
    start: datetime
    end: datetime
    courts_id: int


class TimeBlockUpdate(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    courts_id: Optional[int] = None


class TimeBlock(TimeBlockCreate):
    time_block_id: int

    class Config:
        from_attributes = True
