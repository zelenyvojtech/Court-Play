# app/pages/time_blocks.py
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Form, Path, Request, status
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


def _render_form(
    request: Request,
    user: AuthUser,
    courts: List[Court],
    mode: str,
    block: Optional[TimeBlock] = None,
    error: Optional[str] = None,
) -> HTMLResponse:
    return templates.TemplateResponse(
        "time_blocks/form.html",
        {
            "request": request,
            "user": user,
            "block": block,
            "courts": courts,
            "mode": mode,   # "create" | "edit"
            "error": error,
        },
    )


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
        {"request": request, "user": current_user, "blocks": blocks, "courts": courts},
    )


@router.get("/admin/time-blocks/new", response_class=HTMLResponse)
def time_block_new_form(
    request: Request,
    current_user: AuthUser = Depends(require_manager),
    courts_service: CourtsService = Depends(get_courts_service),
):
    courts: List[Court] = courts_service.list_courts()
    return _render_form(request, current_user, courts, mode="create", block=None, error=None)


@router.post("/admin/time-blocks/new")
def time_block_new_submit(
    request: Request,
    current_user: AuthUser = Depends(require_manager),
    time_block_service: TimeBlockService = Depends(get_time_block_service),
    courts_service: CourtsService = Depends(get_courts_service),
    courts_id: int = Form(...),
    start_datetime: str = Form(...),
    end_datetime: str = Form(...),
):
    courts: List[Court] = courts_service.list_courts()

    try:
        start = datetime.fromisoformat(start_datetime)
        end = datetime.fromisoformat(end_datetime)
    except ValueError:
        return _render_form(request, current_user, courts, "create", None, "Neplatný formát data/času.")

    if end <= start:
        return _render_form(request, current_user, courts, "create", None, "Konec blokace musí být po začátku.")

    block_create = TimeBlockCreate(start=start, end=end, courts_id=courts_id)
    time_block_service.create_time_block(block_create)

    return RedirectResponse(url="/admin/time-blocks", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/admin/time-blocks/{time_block_id:int}/edit", response_class=HTMLResponse)
def time_block_edit_form(
    request: Request,
    time_block_id: int = Path(...),
    current_user: AuthUser = Depends(require_manager),
    time_block_service: TimeBlockService = Depends(get_time_block_service),
    courts_service: CourtsService = Depends(get_courts_service),
):
    block = time_block_service.get_time_block(time_block_id)
    if block is None:
        return RedirectResponse(url="/admin/time-blocks", status_code=status.HTTP_303_SEE_OTHER)

    courts: List[Court] = courts_service.list_courts()
    return _render_form(request, current_user, courts, mode="edit", block=block, error=None)


@router.post("/admin/time-blocks/{time_block_id:int}/edit")
def time_block_edit_submit(
    request: Request,
    time_block_id: int = Path(...),
    current_user: AuthUser = Depends(require_manager),
    time_block_service: TimeBlockService = Depends(get_time_block_service),
    courts_service: CourtsService = Depends(get_courts_service),
    courts_id: int = Form(...),
    start_datetime: str = Form(...),
    end_datetime: str = Form(...),
):
    courts: List[Court] = courts_service.list_courts()
    block = time_block_service.get_time_block(time_block_id)
    if block is None:
        return RedirectResponse(url="/admin/time-blocks", status_code=status.HTTP_303_SEE_OTHER)

    try:
        start = datetime.fromisoformat(start_datetime)
        end = datetime.fromisoformat(end_datetime)
    except ValueError:
        return _render_form(request, current_user, courts, "edit", block, "Neplatný formát data/času.")

    if end <= start:
        return _render_form(request, current_user, courts, "edit", block, "Konec blokace musí být po začátku.")

    update = TimeBlockUpdate(start=start, end=end, courts_id=courts_id)
    if time_block_service.update_time_block(time_block_id, update) is None:
        return _render_form(request, current_user, courts, "edit", block, "Blokace nenalezena.")

    return RedirectResponse(url="/admin/time-blocks", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/admin/time-blocks/{time_block_id:int}/delete")
def time_block_delete(
    time_block_id: int = Path(...),
    current_user: AuthUser = Depends(require_manager),
    time_block_service: TimeBlockService = Depends(get_time_block_service),
):
    time_block_service.delete_time_block(time_block_id)
    return RedirectResponse(url="/admin/time-blocks", status_code=status.HTTP_303_SEE_OTHER)
