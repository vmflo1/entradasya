"""Chequeo de salud. notifications no tiene base de datos: revisa que el servidor de correo responda."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.services.mailer import smtp_ok

router = APIRouter(tags=["salud"])


@router.get("/health")
def health():
    if smtp_ok():
        return {"status": "ok", "servicio": settings.service_name, "smtp": "ok"}
    return JSONResponse(
        status_code=503,
        content={"status": "error", "servicio": settings.service_name, "smtp": "sin conexión"},
    )
