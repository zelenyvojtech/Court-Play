# pages/users.py
from typing import List

from fastapi import APIRouter, Depends, Form, HTTPException, Path, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from dependencies import require_admin, get_users_service

from services.auth import AuthUser
from services.users import UsersService
from model.User import User, UserUpdate

router = APIRouter(tags=["users"])

templates = Jinja2Templates(directory="templates")

ALLOWED_ROLES = {"USER", "MANAGER", "ADMIN"}

# GET /admin/users – seznam všech uživatelů (jen pro ADMIN)
@router.get("/admin/users", response_class=HTMLResponse)
def users_list_page(
    request: Request,
    current_user: AuthUser = Depends(require_admin),
    users_service: UsersService = Depends(get_users_service),
):
    users: List[User] = users_service.list_users()
    return templates.TemplateResponse(
        "users/list.html",
        {
            "request": request,
            "user": current_user,
            "users": users,
        },
    )

# GET /admin/users/{user_id:int}/role – úprava role uživatele (jen pro ADMIN)
@router.post("/admin/users/{user_id:int}/role", name="admin_user_role_update")
def admin_user_role_update(
    request: Request,
    user_id: int = Path(...),
    role: str = Form(...),
    current_user = Depends(require_admin),
    users_service: UsersService = Depends(get_users_service),
):
    role_norm = role.strip().upper()
    if role_norm not in ALLOWED_ROLES:
        return RedirectResponse(url="/admin/users", status_code=status.HTTP_303_SEE_OTHER)

    users_service.update_user(user_id, UserUpdate(role=role_norm))

    return RedirectResponse(url="/admin/users", status_code=status.HTTP_303_SEE_OTHER)