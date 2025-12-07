# pages/auth.py
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from dependencies import (
    get_auth_service,
    get_users_service,
    get_current_user,
)
from services.auth import AuthService, AuthUser
from services.users import UsersService
from services.session import SESSION_COOKIE_NAME, session_store
from model.User import UserCreate

router = APIRouter(tags=["auth"])

templates = Jinja2Templates(directory="templates")


# GET /login – zobrazí přihlašovací formulář, přihlášené uživatele přesměruje na dashboard
@router.get("/login", response_class=HTMLResponse)
def login_form(
    request: Request,
    current_user: Optional[AuthUser] = Depends(get_current_user),
):
    if current_user is not None:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        "auth/login.html",
        {
            "request": request,
            "error": None,
        },
    )


# POST /login – zpracuje login formulář, ověří uživatele a založí session cookie
@router.post("/login")
def login_submit(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    auth_service: AuthService = Depends(get_auth_service),
):
    user = auth_service.authenticate(email=email, password=password)
    if user is None:
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "error": "Neplatný email nebo heslo.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    session_id = session_store.create_session(user)

    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        samesite="lax",
        # secure=True  # pro produkci na HTTPS
    )
    return response


# POST /logout – odhlásí uživatele, smaže session a vyčistí session cookie
@router.post("/logout")
def logout(request: Request):
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    session_store.delete_session(session_id)

    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response


# GET /register – zobrazí registrační formulář, přihlášené uživatele přesměruje na dashboard
@router.get("/register", response_class=HTMLResponse)
def register_form(
    request: Request,
    current_user: Optional[AuthUser] = Depends(get_current_user),
):
    if current_user is not None:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        "auth/register.html",
        {
            "request": request,
            "error": None,
        },
    )


# POST /register – zpracuje registraci, vytvoří hráče (PLAYER) a rovnou ho přihlásí
@router.post("/register")
def register_submit(
    request: Request,
    email: str = Form(...),
    user_name: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    auth_service: AuthService = Depends(get_auth_service),
    users_service: UsersService = Depends(get_users_service),
):
    if password != password_confirm:
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "error": "Hesla se neshodují.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    existing = users_service.get_user_by_email(email)
    if existing is not None:
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "error": "Uživatel s tímto emailem už existuje.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    password_hash = auth_service.hash_password(password)

    user_create = UserCreate(
        email=email,
        user_name=user_name,
        password=password_hash,
        role="PLAYER",  # výchozí role pro nového uživatele
    )

    user = users_service.create_user(user_create)

    # auto-login po registraci
    auth_user = AuthUser(
        user_id=user.user_id,
        email=user.email,
        user_name=user.user_name,
        role=user.role,
    )
    session_id = session_store.create_session(auth_user)

    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        samesite="lax",
    )
    return response
