# pages/dashboard.py
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from dependencies import (
    require_user,
    get_courts_service,
    get_reservations_service,
)
from services import AuthUser, CourtsService, ReservationsService
from model import Court, Reservation

router = APIRouter(tags=["dashboard"])

templates = Jinja2Templates(directory="templates")


# GET / – domovská stránka s přehledem kurtů a rezervací (pro hráče i manažery)
@router.get("/", response_class=HTMLResponse)
def dashboard_page(
    request: Request,
    current_user: AuthUser = Depends(require_user),
    courts_service: CourtsService = Depends(get_courts_service),
    reservations_service: ReservationsService = Depends(get_reservations_service),
):
    courts: List[Court] = courts_service.list_courts()

    my_reservations: List[Reservation] = reservations_service.list_reservations_for_user(
        current_user.user_id
    )

    all_reservations: Optional[List[Reservation]] = None
    if current_user.role in ("MANAGER", "ADMIN"):
        all_reservations = reservations_service.list_future_reservations(
            now=datetime.now()
        )

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": current_user,
            "courts": courts,
            "my_reservations": my_reservations,
            "all_reservations": all_reservations,
        },
    )
