"""Servicio checkin: control de ingreso en la puerta (cada entrada sirve una sola vez)."""
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.connection import run_migrations
from app.routers import health, ingresos

setup_logging(settings.log_level)
log = logging.getLogger("checkin")


@asynccontextmanager
async def lifespan(_: FastAPI):
    run_migrations()
    log.info("Servicio %s listo en el puerto %s", settings.service_name, settings.port)
    yield


app = FastAPI(title="EntradasYa - checkin", lifespan=lifespan)
app.include_router(health.router)
app.include_router(ingresos.router)


if __name__ == "__main__":
    uvicorn.run(app, host=settings.host, port=settings.port, log_config=None)
