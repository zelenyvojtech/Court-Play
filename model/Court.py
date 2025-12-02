from pydantic import BaseModel, Field
from typing import Optional


class CourtCreate(BaseModel):
    court_name: str = Field(min_length=1, max_length=100)
    # v DB INTEGER (0/1), v appce bool – v repository to převedeme na 0/1
    outdoor: bool
    status: str = Field(min_length=1, max_length=50)
    note: Optional[str] = None


class CourtUpdate(BaseModel):
    court_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    outdoor: Optional[bool] = None
    status: Optional[str] = Field(default=None, min_length=1, max_length=50)
    note: Optional[str] = None


class Court(CourtCreate):
    courts_id: int  # primární klíč z tabulky courts

    class Config:
        from_attributes = True
