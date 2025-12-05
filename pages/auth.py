# pages/auth.py
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from dependencies import (
    get_auth_service,
    get_current_user,
)
from services import AuthService, AuthUser, SESSION_COOKIE_NAME, session_store

router = APIRouter(tags=["auth"])

templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse)
def login_form(
    request: Request,
    current_user: Optional[AuthUser] = Depends(get_current_user),
):
    """
    Zobrazí login formulář.
    - pokud je uživatel už přihlášený, přesměruje ho na homepage (/).
    """
    if current_user is not None:
        return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse(
        "auth/login.html",  # budeš potřebovat template templates/auth/login.html
        {
            "request": request,
            "error": None,
        },
    )


@router.post("/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Zpracuje login formulář:
    - ověří credentials přes AuthService.authenticate
    - při neúspěchu vrátí login stránku s chybou
    - při úspěchu vytvoří session, nastaví cookie a přesměruje na homepage
    """
    user = auth_service.authenticate(email=email, password=password)
    if user is None:
        # špatné přihlášení – vracíme formulář se zprávou
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "error": "Neplatný email nebo heslo.",
            },
            status_code=400,
        )

    # úspěšný login – vytvoříme session
    session_id = session_store.create_session(user)

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        samesite="lax",
        # secure=True  # v produkci přes HTTPS; pro lokální vývoj klidně vynech
    )
    return response


@router.post("/logout")
def logout(request: Request):
    """
    Odhlásí uživatele:
    - smaže session ze SessionStore
    - odstraní session cookie
    - přesměruje na login
    """
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    session_store.delete_session(session_id)

    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response
