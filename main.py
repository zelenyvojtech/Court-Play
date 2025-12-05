# main.py
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from pages import auth, account, dashboard, courts, reservations, price_list, time_blocks, users

app = FastAPI(title="Court & Play")

if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


app.include_router(auth.router)
app.include_router(account.router)
app.include_router(dashboard.router)
app.include_router(courts.router)
app.include_router(reservations.router)
app.include_router(price_list.router)
app.include_router(time_blocks.router)
app.include_router(users.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
