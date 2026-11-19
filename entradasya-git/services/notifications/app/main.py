"""Servicio notifications: envío de correos (interno, v1 con Mailpit)."""
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import setup_logging
from app.routers import correos, health

setup_logging(settings.log_level)
log = logging.getLogger("notifications")


@asynccontextmanager
async def lifespan(_: FastAPI):
    log.info("Servicio %s listo en el puerto %s", settings.service_name, settings.port)
    yield


app = FastAPI(title="EntradasYa - notifications", lifespan=lifespan)
app.include_router(health.router)
app.include_router(correos.router)


if __name__ == "__main__":
    uvicorn.run(app, host=settings.host, port=settings.port, log_config=None)
