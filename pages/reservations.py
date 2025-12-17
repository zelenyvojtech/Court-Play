# app/pages/reservations.py
from datetime import date, datetime, time, timedelta
from typing import Optional

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

router = APIRouter(prefix="/app", tags=["Reservations"])

templates = Jinja2Templates(directory="templates")


# --- Pomocná funkce pro výběr ceníku ---
def _pick_price_list_id(
        price_list_service: PriceListService,
        duration_min: int,
        start_dt: datetime,
        end_dt: datetime,
) -> Optional[int]:
    """
    Najde správné ID ceníku podle délky hry a času.
    Kontroluje, zda rezervace spadá do otevírací doby v ceníku.
    """
    start_t = start_dt.time()
    end_t = end_dt.time()

    for item in price_list_service.list_price_lists():
        if item.duration_min != duration_min:
            continue
        # Kontrola, zda je čas v rozmezí platnosti ceníku
        if item.opening_time <= start_t and end_t <= item.closing_time:
            return item.price_list_id
    return None


# ==========================================
# 1. ZOBRAZENÍ KALENDÁŘE (GET)
# ==========================================
@router.get("/kalendar", name="reservations_calendar_ui")
async def reservations_calendar_ui(
        request: Request,
        current_user: AuthUser = Depends(require_user),
        reservations_service: ReservationsService = Depends(get_reservations_service),
        courts_service: CourtsService = Depends(get_courts_service),
):
    # Načtení filtrů z URL (query params)
    q = request.query_params
    flash_ok = q.get("ok")
    flash_error = q.get("error")

    try:
        day = date.fromisoformat(q.get("date")) if q.get("date") else date.today()
    except ValueError:
        day = date.today()
    selected_date = day.isoformat()

    # Validace délky (default 60 min)
    try:
        duration = int(q.get("duration") or 60)
    except ValueError:
        duration = 60
    if duration not in (60, 90, 120):
        duration = 60

    environment = (q.get("env") or "all").lower()

    # Načtení a filtrování kurtů
    all_courts = list(courts_service.list_courts() or [])
    courts = []
    for c in all_courts:
        if environment == "indoor" and c.outdoor: continue
        if environment == "outdoor" and not c.outdoor: continue
        courts.append(c)

    # Generování časových slotů (po 30 min)
    slot_minutes = 30
    opening = datetime.combine(day, time(7, 0))
    closing = datetime.combine(day, time(22, 0))

    time_slots = []
    curr = opening
    while curr < closing:
        time_slots.append(curr.strftime("%H:%M"))
        curr += timedelta(minutes=slot_minutes)

    # Inicializace mřížky (Grid)
    # grid[court_id_str][hhmm] = {status: '...', label: '...'}
    grid = {str(c.courts_id): {} for c in courts}
    now = datetime.now()

    # A) Označení minulosti
    if day < now.date():
        for c in courts:
            for hhmm in time_slots:
                grid[str(c.courts_id)][hhmm] = {"status": "past", "label": "—"}
    elif day == now.date():
        for hhmm in time_slots:
            hh, mm = map(int, hhmm.split(":"))
            if datetime.combine(day, time(hh, mm)) <= now:
                for c in courts:
                    grid[str(c.courts_id)][hhmm] = {"status": "past", "label": "—"}

    # B) Načtení blokací (údržba)
    for c in courts:
        blocks = reservations_service.list_time_blocks_for_court_between(c.courts_id, opening, closing)
        for b in blocks:
            tmp = b.start
            while tmp < b.end:
                hm = tmp.strftime("%H:%M")
                # Pokud je slot v našem seznamu časů, označíme ho jako blocked
                if hm in time_slots:
                    grid[str(c.courts_id)][hm] = {"status": "blocked", "label": "Údržba"}
                tmp += timedelta(minutes=slot_minutes)

    # C) Načtení existujících rezervací
    for c in courts:
        res = reservations_service.list_reservations_for_court_between(c.courts_id, opening, closing)
        for r in res:
            tmp = r.start
            while tmp < r.end:
                hm = tmp.strftime("%H:%M")
                if hm in time_slots:
                    status_key = "mine" if r.user_id == current_user.user_id else "busy"
                    label = "Moje" if status_key == "mine" else "Obsazeno"

                    # Přepíšeme i 'past', pokud tam byla moje rezervace (chci ji vidět zpětně)
                    grid[str(c.courts_id)][hm] = {"status": status_key, "label": label}
                tmp += timedelta(minutes=slot_minutes)

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
            "flash_ok": flash_ok,
            "flash_error": flash_error,
        },
    )


# ==========================================
# 2. POTVRZENÍ REZERVACE (GET)
# ==========================================
@router.get("/rezervace/confirm", name="reservation_confirm_ui")
async def reservation_confirm_ui(
        request: Request,
        court_id: int,
        start: str,  # Očekáváme ISO string (např. 2025-05-20T14:00)
        duration: int,
        current_user: AuthUser = Depends(require_user),
        courts_service: CourtsService = Depends(get_courts_service),
        price_list_service: PriceListService = Depends(get_price_list_service),
):
    # 1. Ověření kurtu
    court = courts_service.get_court(court_id)
    if not court:
        return RedirectResponse("/app/kalendar?error=Kurt+neexistuje", status_code=303)

    # 2. Ověření času
    try:
        start_dt = datetime.fromisoformat(start)
    except ValueError:
        return RedirectResponse("/app/kalendar?error=Chybne+datum", status_code=303)

    end_dt = start_dt + timedelta(minutes=duration)

    # 3. Výpočet ceny
    price_list_id = _pick_price_list_id(price_list_service, duration, start_dt, end_dt)

    if price_list_id is None:
        # Pokud administrátor nenastavil cenu pro tuto délku/čas
        return RedirectResponse(
            f"/app/kalendar?date={start_dt.date()}&error=Pro+tuto+delku+neexistuje+cenik",
            status_code=303
        )

    pl_item = price_list_service.get_price_list(price_list_id)
    multiplier = pl_item.indoor_multiplier if not court.outdoor else 1.0
    final_price = pl_item.base_price * multiplier

    # 4. Zobrazení potvrzovací šablony
    return templates.TemplateResponse(
        "reservations/confirm.html",
        {
            "request": request,
            "user": current_user,
            "court": court,
            "start": start_dt,
            "end": end_dt,
            "duration": duration,
            "price": final_price,
            "price_list_id": price_list_id,
        },
    )


# ==========================================
# 3. VYTVOŘENÍ REZERVACE (POST)
# ==========================================
@router.post("/rezervace/create", name="reservation_create_submit")
async def reservation_create_submit(
        request: Request,
        court_id: int = Form(...),
        start: str = Form(...),
        duration: int = Form(...),
        price_list_id: int = Form(...),
        current_user: AuthUser = Depends(require_user),
        reservations_service: ReservationsService = Depends(get_reservations_service),
):
    try:
        start_dt = datetime.fromisoformat(start)
        end_dt = start_dt + timedelta(minutes=duration)

        # Vytvoření objektu pro rezervaci
        data = ReservationCreate(
            user_id=current_user.user_id,
            price_list_id=price_list_id,
            courts_id=court_id,
            start=start_dt,
            end=end_dt,
            state="CONFIRMED",
        )

        # Uložení do DB (včetně kontroly kolizí a výpočtu ceny)
        reservations_service.create_reservation(data)

    except ValueError as ve:
        # Chyba validace (např. obsazeno)
        return RedirectResponse(f"/app/kalendar?error={ve}", status_code=303)
    except Exception as e:
        # Jiná chyba
        return RedirectResponse(f"/app/kalendar?error=Chyba: {e}", status_code=303)

    return RedirectResponse(
        url=f"/app/kalendar?date={start_dt.date()}&ok=Rezervace+byla+uspesne+vytvorena",
        status_code=303
    )


# ==========================================
# 4. MOJE REZERVACE A STORNO
# ==========================================
@router.get("/moje", name="my_reservations_ui")
async def my_reservations_ui(
        request: Request,
        current_user: AuthUser = Depends(require_user),
        reservations_service: ReservationsService = Depends(get_reservations_service),
        courts_service: CourtsService = Depends(get_courts_service),
):
    reservations = reservations_service.list_reservations_for_user(current_user.user_id)

    all_courts = courts_service.list_courts()
    court_map = {c.courts_id: c.court_name for c in all_courts}

    return templates.TemplateResponse(
        "reservations/my_reservations.html",
        {"request": request, "user": current_user, "reservations": reservations, "court_map": court_map, "now": datetime.now()}
    )


@router.post("/moje/{reservation_id}/cancel", name="my_reservation_cancel")
async def my_reservation_cancel(
        request: Request,
        reservation_id: int,
        current_user: AuthUser = Depends(require_user),
        reservations_service: ReservationsService = Depends(get_reservations_service),
):
    r = reservations_service.get_reservation(reservation_id)
    if not r or r.user_id != current_user.user_id:
        raise HTTPException(status_code=404)

    if getattr(r, "state", None) == "CANCELLED":
        return RedirectResponse(
            url=str(request.url_for("my_reservations_ui").include_query_params(ok="Rezervace už byla zrušena.")),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    # Kontrola času (např. nejde zrušit minulou)
    if r.start <= datetime.now():
        return RedirectResponse(
            url=str(request.url_for("my_reservations_ui").include_query_params(
                error="Nelze zrušit již probíhající rezervaci.")),
            status_code=status.HTTP_303_SEE_OTHER,
        )

    if not reservations_service.cancel_reservation(reservation_id):
        raise HTTPException(status_code=404)

    return RedirectResponse(
        url=str(request.url_for("my_reservations_ui").include_query_params(ok="Rezervace stornována.")),
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/sprava/{reservation_id}/cancel", name="reservation_admin_cancel")
async def reservation_admin_cancel(
        request: Request,
        reservation_id: int,
        current_user: AuthUser = Depends(require_user),
        reservations_service: ReservationsService = Depends(get_reservations_service),
):
    if current_user.role not in ("MANAGER", "ADMIN"):
        raise HTTPException(status_code=403)

    r = reservations_service.get_reservation(reservation_id)
    if not r:
        raise HTTPException(status_code=404)

    if not reservations_service.cancel_reservation(reservation_id):
        raise HTTPException(status_code=404)

    return RedirectResponse(
        url=str(request.url_for("dashboard_ui").include_query_params(ok="Rezervace (admin) stornována.")),
        status_code=status.HTTP_303_SEE_OTHER,
    )