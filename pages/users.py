# pages/users.py
from typing import List

from fastapi import APIRouter, Depends, Form, HTTPException, Path, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from dependencies import require_admin, get_users_service
from services import AuthUser, UsersService
from model import User, UserUpdate

router = APIRouter(tags=["users"])

templates = Jinja2Templates(directory="templates")


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


# GET /admin/users/{id} – detail konkrétního uživatele (jen pro ADMIN)
@router.get("/admin/users/{user_id}", response_class=HTMLResponse)
def user_detail_page(
    request: Request,
    user_id: int = Path(...),
    current_user: AuthUser = Depends(require_admin),
    users_service: UsersService = Depends(get_users_service),
):
    view_user = users_service.get_user(user_id)
    if view_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uživatel nenalezen.")

    return templates.TemplateResponse(
        "users/detail.html",
        {
            "request": request,
            "user": current_user,
            "view_user": view_user,
        },
    )


# GET /admin/users/{id}/edit – formulář pro změnu role uživatele (jen ADMIN)
@router.get("/admin/users/{user_id}/edit", response_class=HTMLResponse)
def user_edit_form(
    request: Request,
    user_id: int = Path(...),
    current_user: AuthUser = Depends(require_admin),
    users_service: UsersService = Depends(get_users_service),
):
    edit_user = users_service.get_user(user_id)
    if edit_user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uživatel nenalezen.")

    return templates.TemplateResponse(
        "users/form.html",
        {
            "request": request,
            "user": current_user,
            "edit_user": edit_user,
            "error": None,
        },
    )


# POST /admin/users/{id}/edit – uloží změnu role uživatele
@router.post("/admin/users/{user_id}/edit")
def user_edit_submit(
    request: Request,
    user_id: int = Path(...),
    current_user: AuthUser = Depends(require_admin),
    users_service: UsersService = Depends(get_users_service),
    role: str = Form(...),
):
    update = UserUpdate(role=role)
    if users_service.update_user(user_id, update) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uživatel nenalezen.")

    return RedirectResponse(
        url=f"/admin/users/{user_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
