# main.py
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from pages.public import router as public_router
from pages.auth import router as auth_router
from pages.accounts import router as account_router
from pages.dashboard import router as dashboard_router
from pages.courts import router as courts_router
from pages.reservations import router as reservations_router
from pages.price_list import router as price_list_router
from pages.time_blocks import router as time_blocks_router
from pages.users import router as users_router

app = FastAPI(title="Court & Play")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(public_router)        # veřejné stránky
app.include_router(auth_router)          # login/registrace
app.include_router(account_router)
app.include_router(dashboard_router)
app.include_router(courts_router)
app.include_router(reservations_router)
app.include_router(price_list_router)
app.include_router(time_blocks_router)
app.include_router(users_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
