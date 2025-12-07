# app/pages/public.py
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from dependencies import get_current_user, require_user
from services.auth import AuthUser

router = APIRouter(tags=["Public"])
templates = Jinja2Templates(directory="templates")


@router.get("/", name="home_page")
async def home_page(
    request: Request,
    current_user: AuthUser | None = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "public/home.html",
        {
            "request": request,
            "user": current_user,
        },
    )


@router.get("/o-klubu", name="about_page")
async def about_page(
    request: Request,
    current_user: AuthUser | None = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "public/about.html",
        {
            "request": request,
            "user": current_user,
        },
    )


@router.get("/tenis", name="tenis_page")
async def tenis_page(
    request: Request,
    current_user: AuthUser | None = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "public/tenis.html",
        {
            "request": request,
            "user": current_user,
        },
    )


@router.get("/cenik", name="public_pricing_page")
async def public_pricing_page(
    request: Request,
    current_user: AuthUser | None = Depends(get_current_user),
):
    # pokud nechceš dynamiku, klidně vrať šablonu jen s natvrdo napsaným ceníkem
    return templates.TemplateResponse(
        "public/pricing.html",
        {
            "request": request,
            "user": current_user,
        },
    )


@router.get("/kontakt", name="contact_page")
async def contact_page(
    request: Request,
    current_user: AuthUser | None = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "public/contact.html",
        {
            "request": request,
            "user": current_user,
        },
    )


@router.get("/rezervace", name="reservations_entry")
async def reservations_entry(
    request: Request,
    current_user: AuthUser | None = Depends(get_current_user),
):
    if current_user is None:
        # nepřihlášený → pošli na login
        return RedirectResponse(
            url=request.url_for("login_ui"),  # podle jména routy v auth.py
            status_code=303,
        )
    # přihlášený → na kalendář / dashboard
    return RedirectResponse(
        url=request.url_for("reservations_calendar_ui"),  # viz níže
        status_code=303,
    )