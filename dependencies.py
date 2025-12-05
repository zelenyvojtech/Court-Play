# dependencies.py
import sqlite3
from typing import Generator, Optional

from fastapi import Depends, HTTPException, Request, status

from database.database import open_connection  # uprav, pokud se u tebe jmenuje jinak
from services import (
    AuthService,
    AuthUser,
    CourtsService,
    PriceListService,
    ReservationsService,
    TimeBlockService,
    UsersService,
    session_store,
    SESSION_COOKIE_NAME,
)


# ---------- DB CONNECTION ----------


def get_conn() -> Generator[sqlite3.Connection, None, None]:
    """
    FastAPI dependency pro získání SQLite connection.

    Používá context manager z database.database (open_connection),
    takže se connection po requestu zase zavře.
    """
    with open_connection() as conn:
        yield conn


# ---------- SERVICES FACTORIES ----------


def get_auth_service(conn: sqlite3.Connection = Depends(get_conn)) -> AuthService:
    return AuthService(conn)


def get_courts_service(conn: sqlite3.Connection = Depends(get_conn)) -> CourtsService:
    return CourtsService(conn)


def get_price_list_service(
    conn: sqlite3.Connection = Depends(get_conn),
) -> PriceListService:
    return PriceListService(conn)


def get_reservations_service(
    conn: sqlite3.Connection = Depends(get_conn),
) -> ReservationsService:
    return ReservationsService(conn)


def get_time_block_service(
    conn: sqlite3.Connection = Depends(get_conn),
) -> TimeBlockService:
    return TimeBlockService(conn)


def get_users_service(conn: sqlite3.Connection = Depends(get_conn)) -> UsersService:
    return UsersService(conn)


# ---------- AUTH / CURRENT USER ----------


def get_current_user(request: Request) -> Optional[AuthUser]:
    """
    Vrátí přihlášeného uživatele ze session (nebo None, pokud není přihlášený).

    - session_id bereme z cookie `SESSION_COOKIE_NAME`
    - data o uživateli čteme z in-memory session_store
    """
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    return session_store.get_user(session_id)


def require_user(
    current_user: Optional[AuthUser] = Depends(get_current_user),
) -> AuthUser:
    """
    Dependency pro endpointy, které vyžadují přihlášeného uživatele.

    - když není přihlášený, vrátíme 401 Unauthorized
      (u pages to můžeš chytnout a přesměrovat na login stránku)
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Musíš být přihlášený.",
        )
    return current_user


def require_manager(
    current_user: AuthUser = Depends(require_user),
) -> AuthUser:
    """
    Dependency pro endpointy, které smí volat jen ROLE: MANAGER nebo ADMIN.
    """
    if current_user.role not in ("MANAGER", "ADMIN"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nemáš oprávnění (vyžadována role MANAGER nebo ADMIN).",
        )
    return current_user


def require_admin(
    current_user: AuthUser = Depends(require_user),
) -> AuthUser:
    """
    Dependency pro endpointy, které smí volat jen ROLE: ADMIN.
    """
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nemáš oprávnění (vyžadována role ADMIN).",
        )
    return current_user
