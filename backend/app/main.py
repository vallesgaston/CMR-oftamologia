import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .config import settings
from .db import Base, SessionLocal, engine
from .routers import anteojos, campanias, consultas, conversaciones, pacientes, turnos, webhook
from .seed import cargar_demo

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crea las tablas que falten. Cuando el esquema empiece a cambiar, pasar a Alembic.
    Base.metadata.create_all(engine)
    if settings.seed_demo:
        with SessionLocal() as db:
            cargar_demo(db)
    yield


app = FastAPI(title="CRM Oftalmología", version="0.1.0", lifespan=lifespan)

for r in (pacientes, turnos, consultas, anteojos, campanias, conversaciones, webhook):
    app.include_router(r.router)


@app.get("/health", tags=["sistema"])
def health():
    return {"ok": True, "whatsapp": "activo" if settings.whatsapp_activo else "simulado"}


@app.get("/", include_in_schema=False)
def raiz():
    # El panel es el proyecto Angular de /frontend (ng serve en el puerto 4200)
    return RedirectResponse("/docs")
