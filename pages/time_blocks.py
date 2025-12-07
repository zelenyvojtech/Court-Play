# pages/time_blocks.py
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Form, HTTPException, Path, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from dependencies import require_manager, get_time_block_service, get_courts_service

from services.auth import AuthUser
from services.time_block import TimeBlockService
from services.courts import CourtsService

from model.TimeBlock import TimeBlock, TimeBlockCreate, TimeBlockUpdate
from model.Court import Court

router = APIRouter(tags=["time_blocks"])

templates = Jinja2Templates(directory="templates")


# GET /admin/time-blocks – přehled všech blokací (údržba kurtů)
@router.get("/admin/time-blocks", response_class=HTMLResponse)
def time_blocks_list_page(
    request: Request,
    current_user: AuthUser = Depends(require_manager),
    time_block_service: TimeBlockService = Depends(get_time_block_service),
    courts_service: CourtsService = Depends(get_courts_service),
):
    blocks: List[TimeBlock] = time_block_service.list_time_blocks()
    courts: List[Court] = courts_service.list_courts()
    return templates.TemplateResponse(
        "time_blocks/list.html",
        {
            "request": request,
            "user": current_user,
            "blocks": blocks,
            "courts": courts,
        },
    )


# GET /admin/time-blocks/new – formulář pro vytvoření nové blokace
@router.get("/admin/time-blocks/new", response_class=HTMLResponse)
def time_block_new_form(
    request: Request,
    current_user: AuthUser = Depends(require_manager),
    courts_service: CourtsService = Depends(get_courts_service),
):
    courts: List[Court] = courts_service.list_courts()
    return templates.TemplateResponse(
        "time_blocks/form.html",
        {
            "request": request,
            "user": current_user,
            "block": None,
            "courts": courts,
            "mode": "create",
            "error": None,
        },
    )


# POST /admin/time-blocks/new – zpracuje vytvoření blokace kurtu v čase
@router.post("/admin/time-blocks/new")
def time_block_new_submit(
    request: Request,
    current_user: AuthUser = Depends(require_manager),
    time_block_service: TimeBlockService = Depends(get_time_block_service),
    courts_id: int = Form(...),
    start_datetime: str = Form(...),
    end_datetime: str = Form(...),
):
    try:
        start = datetime.fromisoformat(start_datetime)
        end = datetime.fromisoformat(end_datetime)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Neplatný formát data/času.",
        )

    if end <= start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Konec blokace musí být po začátku.",
        )

    block_create = TimeBlockCreate(
        start=start,
        end=end,
        courts_id=courts_id,
    )
    time_block_service.create_time_block(block_create)

    return RedirectResponse(
        url="/admin/time-blocks",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# GET /admin/time-blocks/{id}/edit – formulář pro úpravu existující blokace
@router.get("/admin/time-blocks/{time_block_id}/edit", response_class=HTMLResponse)
def time_block_edit_form(
    request: Request,
    time_block_id: int = Path(...),
    current_user: AuthUser = Depends(require_manager),
    time_block_service: TimeBlockService = Depends(get_time_block_service),
    courts_service: CourtsService = Depends(get_courts_service),
):
    block = time_block_service.get_time_block(time_block_id)
    if block is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blokace nenalezena.")

    courts: List[Court] = courts_service.list_courts()

    return templates.TemplateResponse(
        "time_blocks/form.html",
        {
            "request": request,
            "user": current_user,
            "block": block,
            "courts": courts,
            "mode": "edit",
            "error": None,
        },
    )


# POST /admin/time-blocks/{id}/edit – uloží změny blokace kurtu
@router.post("/admin/time-blocks/{time_block_id}/edit")
def time_block_edit_submit(
    request: Request,
    time_block_id: int = Path(...),
    current_user: AuthUser = Depends(require_manager),
    time_block_service: TimeBlockService = Depends(get_time_block_service),
    courts_id: int = Form(...),
    start_datetime: str = Form(...),
    end_datetime: str = Form(...),
):
    try:
        start = datetime.fromisoformat(start_datetime)
        end = datetime.fromisoformat(end_datetime)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Neplatný formát data/času.",
        )

    if end <= start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Konec blokace musí být po začátku.",
        )

    update = TimeBlockUpdate(
        start=start,
        end=end,
        courts_id=courts_id,
    )
    if time_block_service.update_time_block(time_block_id, update) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Blokace nenalezena.")

    return RedirectResponse(
        url="/admin/time-blocks",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# POST /admin/time-blocks/{id}/delete – smaže blokaci kurtu
@router.post("/admin/time-blocks/{time_block_id}/delete")
def time_block_delete(
    time_block_id: int = Path(...),
    current_user: AuthUser = Depends(require_manager),
    time_block_service: TimeBlockService = Depends(get_time_block_service),
):
    time_block_service.delete_time_block(time_block_id)
    return RedirectResponse(
        url="/admin/time-blocks",
        status_code=status.HTTP_303_SEE_OTHER,
    )
