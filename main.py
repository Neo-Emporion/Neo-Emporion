import os

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

app = FastAPI(title=os.getenv("APP_NAME", "Neo-Emporion"), version="1.0.0")


@app.get("/")
def inicio():
    return {"mensaje": "Neo-Emporion API funcionando"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": app.version,
        "environment": os.getenv("APP_ENV", "development"),
    }
