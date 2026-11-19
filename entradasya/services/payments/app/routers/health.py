"""Chequeo de salud: indica si el servicio funciona y si tiene conexión a su BD."""
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.connection import db_ok

router = APIRouter(tags=["salud"])


@router.get("/health")
def health():
    if db_ok():
        return {"status": "ok", "servicio": settings.service_name, "db": "ok"}
    return JSONResponse(
        status_code=503,
        content={"status": "error", "servicio": settings.service_name, "db": "sin conexión"},
    )
