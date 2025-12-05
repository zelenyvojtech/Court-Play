# pages/reservations.py
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Path,
    Query,
    Request,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from dependencies import (
    require_user,
    require_manager,
    get_reservations_service,
    get_courts_service,
    get_price_list_service,
)
from services import (
    AuthUser,
    ReservationsService,
    CourtsService,
    PriceListService,
)
from model import Reservation, ReservationCreate, ReservationUpdate, Court, PriceList

router = APIRouter(tags=["reservations"])

templates = Jinja2Templates(directory="templates")


# GET /reservations/me – zobrazí seznam vlastních rezervací aktuálního uživatele
@router.get("/reservations/me", response_class=HTMLResponse)
def my_reservations_page(
    request: Request,
    current_user: AuthUser = Depends(require_user),
    reservations_service: ReservationsService = Depends(get_reservations_service),
):
    reservations: List[Reservation] = reservations_service.list_reservations_for_user(
        current_user.user_id
    )
    return templates.TemplateResponse(
        "reservations/my_list.html",
        {
            "request": request,
            "user": current_user,
            "reservations": reservations,
        },
    )


# GET /reservations/new – formulář pro vytvoření nové rezervace
@router.get("/reservations/new", response_class=HTMLResponse)
def reservation_new_form(
    request: Request,
    current_user: AuthUser = Depends(require_user),
    courts_service: CourtsService = Depends(get_courts_service),
    price_list_service: PriceListService = Depends(get_price_list_service),
):
    courts: List[Court] = courts_service.list_courts()
    price_list_items: List[PriceList] = price_list_service.list_price_lists()

    return templates.TemplateResponse(
        "reservations/form.html",
        {
            "request": request,
            "user": current_user,
            "courts": courts,
            "price_list_items": price_list_items,
            "error": None,
        },
    )


# POST /reservations/new – zpracuje vytvoření rezervace (kolize + cena řeší service)
@router.post("/reservations/new")
def reservation_new_submit(
    request: Request,
    current_user: AuthUser = Depends(require_user),
    reservations_service: ReservationsService = Depends(get_reservations_service),
    courts_service: CourtsService = Depends(get_courts_service),
    price_list_service: PriceListService = Depends(get_price_list_service),
    courts_id: int = Form(...),
    price_list_id: int = Form(...),
    start_datetime: str = Form(...),
):
    """
    start_datetime očekává ISO formát kompatibilní s <input type="datetime-local">,
    např. '2025-01-10T18:00'
    """
    courts: List[Court] = courts_service.list_courts()
    price_list_items: List[PriceList] = price_list_service.list_price_lists()

    try:
        start = datetime.fromisoformat(start_datetime)
    except ValueError:
        return templates.TemplateResponse(
            "reservations/form.html",
            {
                "request": request,
                "user": current_user,
                "courts": courts,
                "price_list_items": price_list_items,
                "error": "Neplatný formát data/času.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    price_item = price_list_service.get_price_list(price_list_id)
    if price_item is None:
        return templates.TemplateResponse(
            "reservations/form.html",
            {
                "request": request,
                "user": current_user,
                "courts": courts,
                "price_list_items": price_list_items,
                "error": "Zvolená položka ceníku neexistuje.",
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    end = start + timedelta(minutes=price_item.duration_min)

    reservation_create = ReservationCreate(
        start=start,
        end=end,
        user_id=current_user.user_id,
        price_list_id=price_list_id,
        courts_id=courts_id,
        state="PENDING",
    )

    try:
        reservations_service.create_reservation(reservation_create)
    except ValueError as exc:
        return templates.TemplateResponse(
            "reservations/form.html",
            {
                "request": request,
                "user": current_user,
                "courts": courts,
                "price_list_items": price_list_items,
                "error": str(exc),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return RedirectResponse(
        url="/reservations/me",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# POST /reservations/{id}/cancel – stornuje budoucí rezervaci aktuálního uživatele
@router.post("/reservations/{reservation_id}/cancel")
def reservation_cancel(
    reservation_id: int = Path(...),
    current_user: AuthUser = Depends(require_user),
    reservations_service: ReservationsService = Depends(get_reservations_service),
):
    reservation = reservations_service.get_reservation(reservation_id)
    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rezervace nenalezena.")

    # může stornovat jen vlastník
    if reservation.user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Rezervaci nelze stornovat.")

    if reservation.start <= datetime.now():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lze stornovat jen budoucí rezervaci.")

    update = ReservationUpdate(state="CANCELLED")
    reservations_service.update_reservation(reservation_id, update)

    return RedirectResponse(
        url="/reservations/me",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# GET /reservations – přehled všech rezervací (jen pro MANAGER/ADMIN, s filtrem podle kurtu)
@router.get("/reservations", response_class=HTMLResponse)
def reservations_list_page(
    request: Request,
    current_user: AuthUser = Depends(require_manager),
    reservations_service: ReservationsService = Depends(get_reservations_service),
    courts_service: CourtsService = Depends(get_courts_service),
    court_filter: Optional[int] = Query(None, alias="courts_id"),
):
    reservations: List[Reservation] = reservations_service.list_reservations()
    courts: List[Court] = courts_service.list_courts()

    if court_filter is not None:
        reservations = [r for r in reservations if r.courts_id == court_filter]

    return templates.TemplateResponse(
        "reservations/list.html",
        {
            "request": request,
            "user": current_user,
            "reservations": reservations,
            "courts": courts,
            "court_filter": court_filter,
        },
    )


# GET /reservations/{id} – detail konkrétní rezervace (jen pro MANAGER/ADMIN)
@router.get("/reservations/{reservation_id}", response_class=HTMLResponse)
def reservation_detail_page(
    request: Request,
    reservation_id: int = Path(...),
    current_user: AuthUser = Depends(require_manager),
    reservations_service: ReservationsService = Depends(get_reservations_service),
):
    reservation = reservations_service.get_reservation(reservation_id)
    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rezervace nenalezena.")

    return templates.TemplateResponse(
        "reservations/detail.html",
        {
            "request": request,
            "user": current_user,
            "reservation": reservation,
        },
    )


# POST /reservations/{id}/state – změní stav rezervace (MANAGER/ADMIN: CONFIRMED/FINISHED/CANCELLED)
@router.post("/reservations/{reservation_id}/state")
def reservation_change_state(
    reservation_id: int = Path(...),
    state: str = Form(...),
    current_user: AuthUser = Depends(require_manager),
    reservations_service: ReservationsService = Depends(get_reservations_service),
):
    update = ReservationUpdate(state=state)
    if reservations_service.update_reservation(reservation_id, update) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rezervace nenalezena.")

    return RedirectResponse(
        url=f"/reservations/{reservation_id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )
