# pages/price_list.py
from typing import List

from fastapi import APIRouter, Depends, Form, HTTPException, Path, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from dependencies import require_manager, require_admin, get_price_list_service

from services.auth import AuthUser
from services.price_list import PriceListService

from model.PriceList import PriceList, PriceListCreate, PriceListUpdate

router = APIRouter(tags=["price_list"])

templates = Jinja2Templates(directory="templates")


# GET /admin/price-list – přehled všech položek ceníku (jen pro MANAGER/ADMIN)
@router.get("/admin/price-list", response_class=HTMLResponse)
def price_list_page(
    request: Request,
    current_user: AuthUser = Depends(require_manager),
    price_list_service: PriceListService = Depends(get_price_list_service),
):
    items: List[PriceList] = price_list_service.list_price_lists()
    return templates.TemplateResponse(
        "price_list/list.html",
        {
            "request": request,
            "user": current_user,
            "items": items,
        },
    )


# GET /admin/price-list/new – formulář pro přidání nové položky ceníku
@router.get("/admin/price-list/new", response_class=HTMLResponse)
def price_list_new_form(
    request: Request,
    current_user: AuthUser = Depends(require_manager),
):
    return templates.TemplateResponse(
        "price_list/form.html",
        {
            "request": request,
            "user": current_user,
            "item": None,
            "mode": "create",
            "error": None,
        },
    )


# POST /admin/price-list/new – zpracuje vytvoření nové položky ceníku
@router.post("/admin/price-list/new")
def price_list_new_submit(
    request: Request,
    current_user: AuthUser = Depends(require_manager),
    price_list_service: PriceListService = Depends(get_price_list_service),
    duration_min: int = Form(...),
    opening_time: str = Form(...),
    closing_time: str = Form(...),
    base_price: float = Form(...),
    indoor_multiplier: float = Form(...),
):
    item_create = PriceListCreate(
        duration_min=duration_min,
        opening_time=opening_time,
        closing_time=closing_time,
        base_price=base_price,
        indoor_multiplier=indoor_multiplier,
    )
    price_list_service.create_price_list(item_create)

    return RedirectResponse(
        url="/admin/price-list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# GET /admin/price-list/{id}/edit – formulář pro úpravu položky ceníku
@router.get("/admin/price-list/{price_list_id}/edit", response_class=HTMLResponse)
def price_list_edit_form(
    request: Request,
    price_list_id: int = Path(...),
    current_user: AuthUser = Depends(require_manager),
    price_list_service: PriceListService = Depends(get_price_list_service),
):
    item = price_list_service.get_price_list(price_list_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Položka ceníku nenalezena.")

    return templates.TemplateResponse(
        "price_list/form.html",
        {
            "request": request,
            "user": current_user,
            "item": item,
            "mode": "edit",
            "error": None,
        },
    )


# POST /admin/price-list/{id}/edit – uloží změny položky ceníku
@router.post("/admin/price-list/{price_list_id}/edit")
def price_list_edit_submit(
    request: Request,
    price_list_id: int = Path(...),
    current_user: AuthUser = Depends(require_manager),
    price_list_service: PriceListService = Depends(get_price_list_service),
    duration_min: int = Form(...),
    opening_time: str = Form(...),
    closing_time: str = Form(...),
    base_price: float = Form(...),
    indoor_multiplier: float = Form(...),
):
    update = PriceListUpdate(
        duration_min=duration_min,
        opening_time=opening_time,
        closing_time=closing_time,
        base_price=base_price,
        indoor_multiplier=indoor_multiplier,
    )
    if price_list_service.update_price_list(price_list_id, update) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Položka ceníku nenalezena.")

    return RedirectResponse(
        url="/admin/price-list",
        status_code=status.HTTP_303_SEE_OTHER,
    )


# POST /admin/price-list/{id}/delete – smaže položku ceníku (jen ADMIN)
@router.post("/admin/price-list/{price_list_id}/delete")
def price_list_delete(
    price_list_id: int = Path(...),
    current_user: AuthUser = Depends(require_admin),
    price_list_service: PriceListService = Depends(get_price_list_service),
):
    price_list_service.delete_price_list(price_list_id)
    return RedirectResponse(
        url="/admin/price-list",
        status_code=status.HTTP_303_SEE_OTHER,
    )
