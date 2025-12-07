# services/auth.py
import sqlite3
from dataclasses import dataclass
from typing import Optional

from passlib.context import CryptContext

from model.User import User as UserModel
from repositories.users import get_user_by_email

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass
class AuthUser:
    """
    Zjednodušený uživatel, který se bude ukládat do session.
    Nepleť si to s Pydantic modelem `model.User` – proto jiné jméno.
    """
    user_id: int
    email: str
    user_name: str
    role: str


class AuthService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def authenticate(self, email: str, password: str) -> Optional[AuthUser]:
        """
        Ověří uživatele podle emailu a hesla.

        - načte uživatele z DB (repositories.users.get_user_by_email)
        - ověří heslo přes bcrypt
        - při úspěchu vrátí AuthUser, jinak None
        """
        user: Optional[UserModel] = get_user_by_email(self.conn, email)
        if not user:
            return None

        if not pwd_context.verify(password, user.password):
            return None

        return AuthUser(
            user_id=user.user_id,
            email=user.email,
            user_name=user.user_name,
            role=user.role,
        )

    def hash_password(self, password: str) -> str:
        """
        Vrátí bcrypt hash hesla – použiješ při registraci / změně hesla.
        """
        return pwd_context.hash(password)
