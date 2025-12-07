# pages/dashboard.py
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from dependencies import get_current_user, require_user, get_courts_service, get_reservations_service
from services.auth import AuthUser
from services.courts import CourtsService
from services.reservations import ReservationsService

router = APIRouter(tags=["dashboard"])

templates = Jinja2Templates(directory="templates")

@router.get("/", name="home_page")
async def home_page(
    request: Request,
    current_user: AuthUser | None = Depends(get_current_user),
):
    """
    Veřejná úvodní stránka – kdokoliv ji může vidět.
    - pokud je uživatel přihlášený, můžeme mu třeba ukázat tlačítko "Přejít na dashboard"
    - pokud není, ukážeme tlačítko "Přihlásit se" / "Registrovat"
    """
    return templates.TemplateResponse(
        "home.html",   # šablonu vytvoříme za chvíli
        {
            "request": request,
            "user": current_user,
        },
    )

@router.get("/dashboard", name="dashboard_ui")
async def dashboard_ui(
    request: Request,
    current_user: AuthUser = Depends(require_user),
    courts_service: CourtsService = Depends(get_courts_service),
    reservations_service: ReservationsService = Depends(get_reservations_service),
):
    # sem si dáš logiku, co už máš – načtení kurtů, rezervací, atd.
    courts = courts_service.get_all()
    my_reservations = reservations_service.get_for_user(current_user.id)
    all_reservations = reservations_service.get_all() if current_user.role in ("MANAGER", "ADMIN") else []

    return templates.TemplateResponse(
        "dashboard/index.html",  # nebo jak se tvá dashboard šablona jmenuje
        {
            "request": request,
            "user": current_user,
            "courts": courts,
            "my_reservations": my_reservations,
            "all_reservations": all_reservations,
        },
    )
