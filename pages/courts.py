# pages/courts.py
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from dependencies import get_courts_service, require_user
from services import CourtsService, AuthUser

router = APIRouter(tags=["courts"])

templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def home_page(
    request: Request,
    current_user: AuthUser = Depends(require_user),
    courts_service: CourtsService = Depends(get_courts_service),
):
    """
    Domovská stránka – přehled všech kurtů.
    - vyžaduje přihlášeného uživatele (PLAYER/MANAGER/ADMIN)
    """
    courts = courts_service.list_courts()

    return templates.TemplateResponse(
        "courts/list.html",  # templates/courts/list.html
        {
            "request": request,
            "user": current_user,
            "courts": courts,
        },
    )


@router.get("/courts", response_class=HTMLResponse)
def courts_list_page(
    request: Request,
    current_user: AuthUser = Depends(require_user),
    courts_service: CourtsService = Depends(get_courts_service),
):
    """
    Alternativní URL pro seznam kurtů – /courts.
    Můžeš ji použít třeba pro navigaci v menu.
    """
    courts = courts_service.list_courts()

    return templates.TemplateResponse(
        "courts/list.html",
        {
            "request": request,
            "user": current_user,
            "courts": courts,
        },
    )
