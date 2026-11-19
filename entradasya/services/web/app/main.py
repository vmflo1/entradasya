"""Servicio web: la interfaz. No guarda datos; el navegador pide todo a los
demás servicios a través de Nginx (rutas /api/...)."""
import logging

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.config import SERVICE_DIR, settings
from app.core.logging import setup_logging
from app.routers import health, pages

setup_logging(settings.log_level)
log = logging.getLogger("web")

app = FastAPI(title="EntradasYa - web", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=SERVICE_DIR / "static"), name="static")
app.include_router(health.router)
app.include_router(pages.router)


if __name__ == "__main__":
    log.info("Servicio %s en el puerto %s", settings.service_name, settings.port)
    uvicorn.run(app, host=settings.host, port=settings.port, log_config=None)
