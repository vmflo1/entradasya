"""Servicio events: catálogo de eventos, sectores y cupos."""
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.connection import run_migrations
from app.routers import eventos, health, organizador

setup_logging(settings.log_level)
log = logging.getLogger("events")


@asynccontextmanager
async def lifespan(_: FastAPI):
    run_migrations()
    settings.images_path.mkdir(parents=True, exist_ok=True)
    log.info("Servicio %s listo en el puerto %s", settings.service_name, settings.port)
    yield


app = FastAPI(title="EntradasYa - events", lifespan=lifespan)
app.include_router(health.router)
app.include_router(eventos.router)
app.include_router(organizador.router)


if __name__ == "__main__":
    uvicorn.run(app, host=settings.host, port=settings.port, log_config=None)
