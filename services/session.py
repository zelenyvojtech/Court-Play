# services/session.py
import secrets
from threading import Lock
from typing import Dict, Optional

from services.auth import AuthUser

SESSION_COOKIE_NAME = "session_id"


class SessionStore:
    """
    Jednoduchý in-memory store:
    session_id -> AuthUser
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, AuthUser] = {}
        self._lock = Lock()

    def create_session(self, user: AuthUser) -> str:
        """
        Vytvoří novou session pro daného uživatele a vrátí session_id.
        """
        session_id = secrets.token_urlsafe(32)
        with self._lock:
            self._sessions[session_id] = user
        return session_id

    def get_user(self, session_id: Optional[str]) -> Optional[AuthUser]:
        """
        Vrátí AuthUser podle session_id, nebo None (není přihlášen).
        """
        if not session_id:
            return None
        with self._lock:
            return self._sessions.get(session_id)

    def delete_session(self, session_id: Optional[str]) -> None:
        """
        Smaže session podle ID (použiješ při logoutu).
        """
        if not session_id:
            return
        with self._lock:
            self._sessions.pop(session_id, None)


session_store = SessionStore()
