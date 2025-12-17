# services/users.py
import sqlite3
from typing import List, Optional

from model.User import User, UserCreate, UserUpdate
from repositories.users import (
    list_users as repo_list_users,
    get_user as repo_get_user,
    get_user_by_email as repo_get_user_by_email,
    create_user as repo_create_user,
    update_user as repo_update_user,
    delete_user as repo_delete_user,
)


class UsersService:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def list_users(self) -> List[User]:
        return repo_list_users(self.conn)

    def get_user(self, user_id: int) -> Optional[User]:
        return repo_get_user(self.conn, user_id)

    def get_user_by_email(self, email: str) -> Optional[User]:
        return repo_get_user_by_email(self.conn, email)

    def create_user(self, data: UserCreate) -> User:
        """
        Očekává, že `data.password` už je hash
        """
        return repo_create_user(self.conn, data)

    def update_user(
        self,
        user_id: int,
        data: UserUpdate,
    ) -> Optional[User]:
        """
        Tady platí: pokud měníš heslo, dej tam už zahashovaný
        `password`.
        """
        return repo_update_user(self.conn, user_id, data)

    def delete_user(self, user_id: int) -> bool:
        return repo_delete_user(self.conn, user_id)
