"""Servicio auth: usuarios, roles e inicio de sesión con JWT."""
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.connection import run_migrations
from app.routers import auth, health

setup_logging(settings.log_level)
log = logging.getLogger("auth")


@asynccontextmanager
async def lifespan(_: FastAPI):
    run_migrations()
    log.info("Servicio %s listo en el puerto %s", settings.service_name, settings.port)
    yield


app = FastAPI(title="EntradasYa - auth", lifespan=lifespan)
app.include_router(health.router)
app.include_router(auth.router)


if __name__ == "__main__":
    uvicorn.run(app, host=settings.host, port=settings.port, log_config=None)
