# main.py
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from pages import auth, courts, reservations

app = FastAPI(title="Court & Play")

if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
app.include_router(courts.router)
app.include_router(reservations.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
