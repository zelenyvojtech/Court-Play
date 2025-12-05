from pydantic import BaseModel, Field
from datetime import time
from typing import Optional


class PriceListCreate(BaseModel):
    duration_min: int = Field(..., gt=0)
    opening_time: time
    closing_time: time
    base_price: float = Field(..., gt=0)
    indoor_multiplier: float = Field(..., gt=0)


class PriceListUpdate(BaseModel):
    duration_min: Optional[int] = Field(default=None, gt=0)
    opening_time: Optional[time] = None
    closing_time: Optional[time] = None
    base_price: Optional[float] = Field(default=None, gt=0)
    indoor_multiplier: Optional[float] = Field(default=None, gt=0)


class PriceList(PriceListCreate):
    price_list_id: int

    class Config:
        from_attributes = True
