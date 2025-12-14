from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    user_name: str = Field(min_length=1, max_length=100)
    role: str = Field(min_length=1, max_length=50)   # "PLAYER", "MANAGER", "ADMIN" ...
    password: str = Field(min_length=8)              # hash


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    user_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    role: Optional[str] = Field(default=None, min_length=1, max_length=50)
    password: Optional[str] = Field(default=None, min_length=8)


class User(BaseModel):
    user_id: int
    email: EmailStr
    user_name: str
    role: str
    created_at: datetime
    password: str  # hash

    class Config:
        from_attributes = True
