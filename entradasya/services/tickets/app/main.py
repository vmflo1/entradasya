"""Servicio tickets: genera y valida las entradas (PDF + QR)."""
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.connection import run_migrations
from app.routers import entradas, health

setup_logging(settings.log_level)
log = logging.getLogger("tickets")


@asynccontextmanager
async def lifespan(_: FastAPI):
    run_migrations()
    settings.tickets_path.mkdir(parents=True, exist_ok=True)
    log.info("Carpeta de PDFs: %s", settings.tickets_path)
    log.info("Servicio %s listo en el puerto %s", settings.service_name, settings.port)
    yield


app = FastAPI(title="EntradasYa - tickets", lifespan=lifespan)
app.include_router(health.router)
app.include_router(entradas.router)


if __name__ == "__main__":
    uvicorn.run(app, host=settings.host, port=settings.port, log_config=None)
