# app/pages/reservations.py
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, Request
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
    q = request.query_params

    try:
        day = date.fromisoformat(q.get("date")) if q.get("date") else date.today()
    except ValueError:
        day = date.today()
    selected_date = day.isoformat()

    try:
        duration = int(q.get("duration") or 60)
    except ValueError:
        duration = 60
    if duration not in (60, 90, 120):
        duration = 60

    environment = (q.get("env") or "all").lower()
    if environment not in ("all", "indoor", "outdoor"):
        environment = "all"

    courts = list(courts_service.list_courts() or [])

    if environment == "indoor":
        courts = [c for c in courts if not getattr(c, "outdoor", False)]
    elif environment == "outdoor":
        courts = [c for c in courts if getattr(c, "outdoor", False)]

    slot_minutes = 30
    opening = datetime.combine(day, time(7, 0))
    closing = datetime.combine(day, time(22, 0))

    time_slots = []
    t = opening
    while t < closing:
        time_slots.append(t.strftime("%H:%M"))
        t += timedelta(minutes=slot_minutes)

    slot_set = set(time_slots)
    step = timedelta(minutes=slot_minutes)

    def round_down(dt: datetime) -> datetime:
        m = dt.minute - (dt.minute % slot_minutes)
        return dt.replace(minute=m, second=0, microsecond=0)

    def round_up(dt: datetime) -> datetime:
        rd = round_down(dt)
        if rd == dt.replace(second=0, microsecond=0):
            return rd
        return rd + timedelta(minutes=slot_minutes)

    grid = {str(getattr(c, "courts_id")): {} for c in courts}

    for c in courts:
        cid = getattr(c, "courts_id")
        cid_s = str(cid)

        blocks = reservations_service.list_time_blocks_for_court_between(cid, opening, closing)
        for b in blocks:
            b_start = round_down(getattr(b, "start"))
            b_end = round_up(getattr(b, "end"))
            cur = b_start
            while cur < b_end:
                hhmm = cur.strftime("%H:%M")
                if hhmm in slot_set:
                    grid[cid_s][hhmm] = {"status": "blocked", "label": "Blokace"}
                cur += step

        res = reservations_service.list_reservations_for_court_between(cid, opening, closing)
        for r in res:
            r_start = round_down(getattr(r, "start"))
            r_end = round_up(getattr(r, "end"))
            r_user_id = getattr(r, "user_id", None)

            status = "mine" if r_user_id == current_user.id else "busy"
            label = "Moje" if status == "mine" else "Obsazeno"

            cur = r_start
            while cur < r_end:
                hhmm = cur.strftime("%H:%M")
                if hhmm in slot_set:

                    if grid[cid_s].get(hhmm, {}).get("status") != "blocked":
                        grid[cid_s][hhmm] = {"status": status, "label": label}
                cur += step

    return templates.TemplateResponse(
        "reservations/calendar.html",
        {
            "request": request,
            "user": current_user,
            "courts": courts,
            "time_slots": time_slots,
            "grid": grid,
            "selected_date": selected_date,
            "duration": duration,
            "environment": environment,
            "slot_minutes": slot_minutes,
        },
    )


@router.get("/moje", name="my_reservations_ui")
async def my_reservations_ui(
    request: Request,
    current_user: AuthUser = Depends(require_user),
    reservations_service: ReservationsService = Depends(get_reservations_service),
):
    reservations = reservations_service.list_reservations_for_user(current_user.id)

    return templates.TemplateResponse(
        "reservations/my_reservations.html",
        {
            "request": request,
            "user": current_user,
            "reservations": reservations,
        },
    )
