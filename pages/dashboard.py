# app/pages/dashboard.py
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from dependencies import require_user, get_courts_service, get_reservations_service
from services.auth import AuthUser
from services.courts import CourtsService
from services.reservations import ReservationsService

router = APIRouter(prefix="/app", tags=["App"])
templates = Jinja2Templates(directory="templates")


@router.get("/dashboard", name="dashboard_ui")
async def dashboard_ui(
    request: Request,
    current_user: AuthUser = Depends(require_user),
    courts_service: CourtsService = Depends(get_courts_service),
    reservations_service: ReservationsService = Depends(get_reservations_service),
):
    courts = courts_service.list_courts()
    my_reservations = reservations_service.get_for_user(current_user.id)
    all_reservations = (
        reservations_service.list_reservations()
        if current_user.role in ("MANAGER", "ADMIN")
        else []
    )

    return templates.TemplateResponse(
        "dashboard/index.html",
        {
            "request": request,
            "user": current_user,
            "courts": courts,
            "my_reservations": my_reservations,
            "all_reservations": all_reservations,
        },
    )
