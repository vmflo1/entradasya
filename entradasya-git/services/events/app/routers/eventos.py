from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.schemas.eventos import (
    EventoDetalleOut,
    EventoResumenOut,
    LiberarOut,
    ReservaIn,
    ReservaOut,
)
from app.services import eventos

router = APIRouter(tags=["eventos"])


@router.get("/eventos", response_model=list[EventoResumenOut])
def cartelera():
    """Cartelera pública: solo eventos publicados."""
    return eventos.listar_publicados()


@router.get("/eventos/{evento_id}", response_model=EventoDetalleOut)
def detalle(evento_id: int):
    return eventos.obtener_publicado(evento_id)


# --- Uso interno de orders (Nginx bloquea estas rutas desde afuera) ---

@router.post("/reservas", response_model=ReservaOut)
def reservar(data: ReservaIn, _: dict = Depends(get_current_user)):
    return eventos.reservar(data.orden_id, data.evento_id, data.sector_id, data.cantidad)


@router.post("/reservas/{orden_id}/liberar", response_model=LiberarOut)
def liberar(orden_id: str, _: dict = Depends(get_current_user)):
    return {"orden_id": orden_id, "liberada": eventos.liberar(orden_id)}
