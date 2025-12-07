# pages/courts.py
from typing import List

from fastapi import APIRouter, Depends, Form, HTTPException, Path, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from dependencies import require_user, require_manager, require_admin, get_courts_service
from services.auth import AuthUser
from services.courts import CourtsService
from model.Court import Court, CourtCreate, CourtUpdate

router = APIRouter(tags=["courts"])

templates = Jinja2Templates(directory="templates")


# GET /courts – zobrazí seznam všech kurtů (pro přihlášené uživatele)
@router.get("/courts", response_class=HTMLResponse)
def courts_list_page(
    request: Request,
    current_user: AuthUser = Depends(require_user),
    courts_service: CourtsService = Depends(get_courts_service),
):
    courts: List[Court] = courts_service.list_courts()
    return templates.TemplateResponse(
        "courts/list.html",
        {
            "request": request,
            "user": current_user,
            "courts": courts,
        },
    )


# GET /courts/{courts_id} – zobrazí detail konkrétního kurtu
@router.get("/courts/{courts_id}", response_class=HTMLResponse)
def court_detail_page(
    request: Request,
    courts_id: int = Path(...),
    current_user: AuthUser = Depends(require_user),
    courts_service: CourtsService = Depends(get_courts_service),
):
    court = courts_service.get_court(courts_id)
    if court is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kurt nenalezen.")

    return templates.TemplateResponse(
        "courts/detail.html",
        {
            "request": request,
            "user": current_user,
            "court": court,
        },
    )


# GET /courts/new – formulář pro vytvoření nového kurtu (jen pro MANAGER/ADMIN)
@router.get("/courts/new", response_class=HTMLResponse)
def court_new_form(
    request: Request,
    current_user: AuthUser = Depends(require_manager),
):
    return templates.TemplateResponse(
        "courts/form.html",
        {
            "request": request,
            "user": current_user,
            "court": None,
            "mode": "create",
            "error": None,
        },
    )


# POST /courts/new – zpracuje vytvoření nového kurtu
@router.post("/courts/new")
def court_new_submit(
    request: Request,
    current_user: AuthUser = Depends(require_manager),
    courts_service: CourtsService = Depends(get_courts_service),
    court_name: str = Form(...),
    outdoor: str = Form(...),
    status_text: str = Form(..., alias="status"),
    note: str | None = Form(None),
):
    outdoor_bool = outdoor.lower() in ("1", "true", "on", "yes")

    court_create = CourtCreate(
        court_name=court_name,
        outdoor=outdoor_bool,
        status=status_text,
        note=note or None,
    )

    courts_service.create_court(court_create)

    return RedirectResponse(url="/courts", status_code=status.HTTP_303_SEE_OTHER)


# GET /courts/{courts_id}/edit – formulář pro úpravu kurtu (jen pro MANAGER/ADMIN)
@router.get("/courts/{courts_id}/edit", response_class=HTMLResponse)
def court_edit_form(
    request: Request,
    courts_id: int = Path(...),
    current_user: AuthUser = Depends(require_manager),
    courts_service: CourtsService = Depends(get_courts_service),
):
    court = courts_service.get_court(courts_id)
    if court is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kurt nenalezen.")

    return templates.TemplateResponse(
        "courts/form.html",
        {
            "request": request,
            "user": current_user,
            "court": court,
            "mode": "edit",
            "error": None,
        },
    )


# POST /courts/{courts_id}/edit – uloží změny kurtu
@router.post("/courts/{courts_id}/edit")
def court_edit_submit(
    request: Request,
    courts_id: int = Path(...),
    current_user: AuthUser = Depends(require_manager),
    courts_service: CourtsService = Depends(get_courts_service),
    court_name: str = Form(...),
    outdoor: str = Form(...),
    status_text: str = Form(..., alias="status"),
    note: str | None = Form(None),
):
    outdoor_bool = outdoor.lower() in ("1", "true", "on", "yes")

    update = CourtUpdate(
        court_name=court_name,
        outdoor=outdoor_bool,
        status=status_text,
        note=note or None,
    )

    if courts_service.update_court(courts_id, update) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Kurt nenalezen.")

    return RedirectResponse(url="/courts", status_code=status.HTTP_303_SEE_OTHER)


# POST /courts/{courts_id}/delete – smaže kurt (povoleno jen ADMIN)
@router.post("/courts/{courts_id}/delete")
def court_delete(
    courts_id: int = Path(...),
    current_user: AuthUser = Depends(require_admin),
    courts_service: CourtsService = Depends(get_courts_service),
):
    courts_service.delete_court(courts_id)
    return RedirectResponse(url="/courts", status_code=status.HTTP_303_SEE_OTHER)
