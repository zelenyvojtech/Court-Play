# pages/account.py
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from dependencies import require_user, get_auth_service, get_users_service
from services import AuthUser, AuthService, UsersService
from model import UserUpdate

router = APIRouter(tags=["account"])

templates = Jinja2Templates(directory="templates")


# GET /profile – zobrazí profil aktuálně přihlášeného uživatele
@router.get("/profile", response_class=HTMLResponse)
def profile_page(
    request: Request,
    current_user: AuthUser = Depends(require_user),
):
    return templates.TemplateResponse(
        "account/profile.html",
        {
            "request": request,
            "user": current_user,
            "error": None,
            "success": None,
        },
    )


# POST /profile – uloží změny v profilu (aktuálně jméno uživatele)
@router.post("/profile")
def profile_update(
    request: Request,
    current_user: AuthUser = Depends(require_user),
    users_service: UsersService = Depends(get_users_service),
    user_name: str = Form(...),
):
    update = UserUpdate(user_name=user_name)
    users_service.update_user(current_user.user_id, update)

    return templates.TemplateResponse(
        "account/profile.html",
        {
            "request": request,
            "user": AuthUser(
                user_id=current_user.user_id,
                email=current_user.email,
                user_name=user_name,
                role=current_user.role,
            ),
            "error": None,
            "success": "Profil byl aktualizován.",
        },
    )


# GET /profile/password – zobrazí formulář pro změnu hesla
@router.get("/profile/password", response_class=HTMLResponse)
def change_password_form(
    request: Request,
    current_user: AuthUser = Depends(require_user),
):
    return templates.TemplateResponse(
        "account/change_password.html",
        {
            "request": request,
            "user": current_user,
            "error": None,
            "success": None,
        },
    )


# POST /profile/password – ověří staré heslo a uloží nové heslo uživatele
@router.post("/profile/password")
def change_password_submit(
    request: Request,
    current_user: AuthUser = Depends(require_user),
    auth_service: AuthService = Depends(get_auth_service),
    users_service: UsersService = Depends(get_users_service),
    current_password: str = Form(...),
    new_password: str = Form(...),
    new_password_confirm: str = Form(...),
):
    if new_password != new_password_confirm:
        return templates.TemplateResponse(
            "account/change_password.html",
            {
                "request": request,
                "user": current_user,
                "error": "Nová hesla se neshodují.",
                "success": None,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # ověření aktuálního hesla
    if auth_service.authenticate(current_user.email, current_password) is None:
        return templates.TemplateResponse(
            "account/change_password.html",
            {
                "request": request,
                "user": current_user,
                "error": "Aktuální heslo je chybné.",
                "success": None,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    password_hash = auth_service.hash_password(new_password)
    update = UserUpdate(password=password_hash)
    users_service.update_user(current_user.user_id, update)

    return templates.TemplateResponse(
        "account/change_password.html",
        {
            "request": request,
            "user": current_user,
            "error": None,
            "success": "Heslo bylo změněno.",
        },
    )
