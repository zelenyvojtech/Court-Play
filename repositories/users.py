# app/repositories/users.py
import sqlite3
from datetime import datetime
from typing import List, Optional

from model.User import User, UserCreate, UserUpdate


def _row_to_user(row: sqlite3.Row) -> User:
    """
    Převede řádek z tabulky users na Pydantic model User.
    TEXT created_at se převede na datetime.
    """
    return User.model_validate(dict(row))


def list_users(conn: sqlite3.Connection) -> List[User]:
    """
    Vrátí všechny uživatele.
    """
    rows = conn.execute(
        """
        SELECT user_id,
               email,
               user_name,
               role,
               created_at,
               password
        FROM users
        ORDER BY user_id
        """
    ).fetchall()
    return [_row_to_user(r) for r in rows]


def get_user(conn: sqlite3.Connection, user_id: int) -> Optional[User]:
    """
    Vrátí jednoho uživatele podle ID nebo None.
    """
    row = conn.execute(
        """
        SELECT user_id,
               email,
               user_name,
               role,
               created_at,
               password
        FROM users
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()
    return _row_to_user(row) if row else None


def get_user_by_email(conn: sqlite3.Connection, email: str) -> Optional[User]:
    """
    Najde uživatele podle emailu – užitečné pro login.
    """
    row = conn.execute(
        """
        SELECT user_id,
               email,
               user_name,
               role,
               created_at,
               password
        FROM users
        WHERE email = ?
        """,
        (email,),
    ).fetchone()
    return _row_to_user(row) if row else None


def create_user(
    conn: sqlite3.Connection,
    data: UserCreate,
    created_at: Optional[datetime] = None,
) -> User:
    """
    Vytvoří nového uživatele.

    - `created_at` pokud nedáš, použije se aktuální čas.
    - `password` zatím bereme jak je (plain text nebo hash – podle toho, co předáš).
    """
    if created_at is None:
        created_at = datetime.now()

    payload = data.model_dump(mode="json")

    cur = conn.execute(
        """
        INSERT INTO users (
            email,
            user_name,
            role,
            created_at,
            password
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            payload["email"],
            payload["user_name"],
            payload["role"],
            created_at.isoformat(),
            payload["password"],
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    return get_user(conn, new_id)


def update_user(
    conn: sqlite3.Connection,
    user_id: int,
    data: UserUpdate,
) -> Optional[User]:
    """
    Update uživatele – dynamicky jen neprázdná pole.

    (typicky budeš měnit jméno, roli, případně heslo)
    """
    update_data = data.model_dump(
        exclude_unset=True,
        exclude_none=True,
        mode="json",
    )

    if not update_data:
        return get_user(conn, user_id)

    set_clause = ", ".join(f"{col} = ?" for col in update_data.keys())
    values = list(update_data.values()) + [user_id]

    cur = conn.execute(
        f"UPDATE users SET {set_clause} WHERE user_id = ?",
        values,
    )
    conn.commit()

    if cur.rowcount == 0:
        return None

    return get_user(conn, user_id)


def delete_user(conn: sqlite3.Connection, user_id: int) -> bool:
    """
    Smaže uživatele podle ID.
    """
    cur = conn.execute(
        "DELETE FROM users WHERE user_id = ?",
        (user_id,),
    )
    conn.commit()
    return cur.rowcount > 0
