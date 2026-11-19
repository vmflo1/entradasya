from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse

from app.core.security import get_current_user, require_roles
from app.schemas.entradas import EntradaOut, GenerarIn, ValidacionOut
from app.services import entradas

router = APIRouter(tags=["entradas"])


# Uso interno de orders (Nginx bloquea esta ruta desde afuera)
@router.post("/entradas/generar", response_model=list[EntradaOut])
def generar(data: GenerarIn, user: dict = Depends(get_current_user)):
    return entradas.generar(user["id"], data.model_dump())


@router.get("/entradas/mias", response_model=list[EntradaOut])
def mias(user: dict = Depends(get_current_user)):
    return entradas.mis_entradas(user["id"])


@router.get("/entradas/{codigo}/pdf")
def descargar(codigo: str, user: dict = Depends(get_current_user)):
    ruta = entradas.ruta_pdf(codigo, user["id"])
    return FileResponse(ruta, media_type="application/pdf", filename=f"entrada-{codigo}.pdf")


# Usado por checkin con el token del portero
@router.get("/entradas/{codigo}/validar", response_model=ValidacionOut)
def validar(codigo: str, evento_id: int | None = Query(default=None),
            _: dict = Depends(require_roles("portero", "organizador"))):
    return entradas.validar(codigo, evento_id)
