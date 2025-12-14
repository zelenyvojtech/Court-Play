# app/pages/reservations.py
from datetime import date, datetime, time, timedelta
import json
from urllib.parse import quote

from fastapi import APIRouter, Depends, Request, Form, status, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from dependencies import (
    require_user,
    get_reservations_service,
    get_courts_service,
    get_price_list_service,
)
from services.auth import AuthUser
from services.reservations import ReservationsService
from services.courts import CourtsService
from services.price_list import PriceListService
from model.Reservation import ReservationCreate

router = APIRouter(tags=["Reservations"])
templates = Jinja2Templates(directory="templates")


def _pick_price_list_id(
    price_list_service: PriceListService,
    duration_min: int,
    start_dt: datetime,
    end_dt: datetime,
) -> int | None:
    """
    Vybere položku ceníku pro danou délku + časové okno.
    Minimalisticky: první match.
    """
    start_t = start_dt.time()
    end_t = end_dt.time()

    for item in price_list_service.list_price_lists():
        if item.duration_min != duration_min:
            continue
        # slot musí spadat do časů ceníku
        if item.opening_time <= start_t and end_t <= item.closing_time:
            return item.price_list_id

    return None

@router.get("/kalendar", name="reservations_calendar_ui")
async def reservations_calendar_ui(
    request: Request,
    current_user: AuthUser = Depends(require_user),
    reservations_service: ReservationsService = Depends(get_reservations_service),
    courts_service: CourtsService = Depends(get_courts_service),
):
    q = request.query_params

    # flash zprávy po redirectu
    flash_ok = q.get("ok")
    flash_error = q.get("error")

    # datum
    try:
        day = date.fromisoformat(q.get("date")) if q.get("date") else date.today()
    except ValueError:
        day = date.today()
    selected_date = day.isoformat()

    # délka (povolíme i 30)
    try:
        duration = int(q.get("duration") or 60)
    except ValueError:
        duration = 60
    if duration not in (30, 60, 90, 120):
        duration = 60

    # filtr indoor/outdoor
    environment = (q.get("env") or "all").lower()
    if environment not in ("all", "indoor", "outdoor"):
        environment = "all"

    courts = list(courts_service.list_courts() or [])
    if environment == "indoor":
        courts = [c for c in courts if not getattr(c, "outdoor", False)]
    elif environment == "outdoor":
        courts = [c for c in courts if getattr(c, "outdoor", False)]

    # časová osa po 30 minutách
    slot_minutes = 30
    opening = datetime.combine(day, time(7, 0))
    closing = datetime.combine(day, time(22, 0))

    time_slots: list[str] = []
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

    # grid[courts_id_str][HH:MM] = {status,label}
    grid = {str(c.courts_id): {} for c in courts}

    for c in courts:
        cid = c.courts_id
        cid_s = str(cid)

        # blokace (time_blocks)
        blocks = reservations_service.list_time_blocks_for_court_between(cid, opening, closing)
        for b in blocks:
            b_start = round_down(b.start)
            b_end = round_up(b.end)
            cur = b_start
            while cur < b_end:
                hhmm = cur.strftime("%H:%M")
                if hhmm in slot_set:
                    grid[cid_s][hhmm] = {"status": "blocked", "label": "Blokace"}
                cur += step

        # rezervace
        res = reservations_service.list_reservations_for_court_between(cid, opening, closing)
        for r in res:
            if getattr(r, "state", None) == "CANCELLED":
                continue

            r_start = round_down(r.start)
            r_end = round_up(r.end)
            r_user_id = getattr(r, "user_id", None)

            status_txt = "mine" if r_user_id == current_user.user_id else "busy"
            label_txt = "Moje" if status_txt == "mine" else "Obsazeno"

            cur = r_start
            while cur < r_end:
                hhmm = cur.strftime("%H:%M")
                if hhmm in slot_set:
                    if grid[cid_s].get(hhmm, {}).get("status") != "blocked":
                        grid[cid_s][hhmm] = {"status": status_txt, "label": label_txt}
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
            "flash_ok": flash_ok,
            "flash_error": flash_error,
        },
    )


@router.post("/kalendar", name="reservations_calendar_submit")
async def reservations_calendar_submit(
    request: Request,
    current_user: AuthUser = Depends(require_user),
    reservations_service: ReservationsService = Depends(get_reservations_service),
    price_list_service: PriceListService = Depends(get_price_list_service),
    selected_slots: str = Form("[]"),
    selected_date: str = Form(..., alias="date"),
    duration: int = Form(60),
    environment: str = Form("all", alias="env"),
):
    # aby se po redirectu zachovaly filtry
    try:
        day = date.fromisoformat(selected_date)
    except ValueError:
        day = date.today()

    if duration not in (30, 60, 90, 120):
        duration = 60

    try:
        slots = json.loads(selected_slots)
        if not isinstance(slots, list):
            slots = []
    except json.JSONDecodeError:
        slots = []

    base = request.url_for("reservations_calendar_ui").include_query_params(
        date=day.isoformat(),
        duration=duration,
        env=environment,
    )

    if not slots:
        return RedirectResponse(
            url=str(base.include_query_params(error="Nevybral(a) jsi žádný termín.")),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    created_ids: list[int] = []

    try:
        for s in slots:
            court_id = int(s.get("court_id"))
            start_hhmm = str(s.get("start"))
            dur = int(s.get("duration", duration))

            # start/end datetime
            try:
                hh, mm = start_hhmm.split(":")
                start_dt = datetime.combine(day, time(int(hh), int(mm)))
            except Exception:
                raise ValueError(f"Neplatný čas: {start_hhmm}")

            end_dt = start_dt + timedelta(minutes=dur)

            price_list_id = _pick_price_list_id(price_list_service, dur, start_dt, end_dt)
            if price_list_id is None:
                raise ValueError(
                    f"Chybí položka ceníku pro {dur} min v čase {start_hhmm}."
                )

            data = ReservationCreate(
                user_id=current_user.user_id,
                price_list_id=price_list_id,
                courts_id=court_id,
                start=start_dt,
                end=end_dt,
                state="CONFIRMED",
            )

            created = reservations_service.create_reservation(data)
            created_ids.append(created.reservation_id)

    except Exception as e:
        for rid in created_ids:
            try:
                reservations_service.delete_reservation(rid)
            except Exception:
                pass

        return RedirectResponse(
            url=base_url + "&error=" + quote(str(e)),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    return RedirectResponse(
        url=str(base.include_query_params(ok=f"Uloženo rezervací: {len(created_ids)}")),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/moje", name="my_reservations_ui")
async def my_reservations_ui(
    request: Request,
    current_user: AuthUser = Depends(require_user),
    reservations_service: ReservationsService = Depends(get_reservations_service),
):
    reservations = reservations_service.list_reservations_for_user(current_user.user_id)

    return templates.TemplateResponse(
        "reservations/my_reservations.html",
        {
            "request": request,
            "user": current_user,
            "reservations": reservations,
            "now": datetime.now(),
        },
    )


@router.post("/moje/{reservation_id}/cancel", name="my_reservation_cancel")
async def cancel_my_reservation(
    request: Request,
    reservation_id: int,
    current_user: AuthUser = Depends(require_user),
    reservations_service: ReservationsService = Depends(get_reservations_service),
):
    mine = reservations_service.list_reservations_for_user(current_user.user_id)
    r = next((x for x in mine if x.reservation_id == reservation_id), None)
    if r is None:
        raise HTTPException(status_code=404)

    now = datetime.now()

    if getattr(r, "state", None) == "CANCELLED":
        return RedirectResponse(
            url=str(request.url_for("my_reservations_ui").include_query_params(ok="Rezervace už je zrušená.")),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    if r.start <= now:
        return RedirectResponse(
            url=str(request.url_for("my_reservations_ui").include_query_params(
                error="Minulou rezervaci už nelze stornovat."
            )),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    updated = reservations_service.cancel_reservation(reservation_id)
    if updated is None:
        raise HTTPException(status_code=404)

    return RedirectResponse(
        url=str(request.url_for("my_reservations_ui").include_query_params(ok="Rezervace stornována.")),
        status_code=status.HTTP_303_SEE_OTHER,
    )
