# app/pages/reservations.py
from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from dependencies import require_user, get_reservations_service, get_courts_service
from services.auth import AuthUser
from services.reservations import ReservationsService
from services.courts import CourtsService

router = APIRouter(prefix="/app/rezervace", tags=["Reservations"])
templates = Jinja2Templates(directory="templates")


@router.get("/kalendar", name="reservations_calendar_ui")
async def reservations_calendar_ui(
    request: Request,
    current_user: AuthUser = Depends(require_user),
    reservations_service: ReservationsService = Depends(get_reservations_service),
    courts_service: CourtsService = Depends(get_courts_service),
):
    # logika pro kalendář – načtení slotů atd.
    ...
    return templates.TemplateResponse(
        "reservations/calendar.html",
        {
            "request": request,
            "user": current_user,
            # slots, selected_date, ...
        },
    )


@router.get("/moje", name="my_reservations_ui")
async def my_reservations_ui(
    request: Request,
    current_user: AuthUser = Depends(require_user),
    reservations_service: ReservationsService = Depends(get_reservations_service),
):
    reservations = reservations_service.get_for_user(current_user.id)
    return templates.TemplateResponse(
        "reservations/my_reservations.html",
        {
            "request": request,
            "user": current_user,
            "reservations": reservations,
        },
    )
