"""Rutas del organizador: solo usuarios con rol organizador, y cada uno solo sobre sus eventos."""
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse

from app.core.security import require_roles
from app.schemas.organizador import EstadoIn, EventoIn, EventoOrgOut, SectorIn
from app.services import imagenes, organizador

router = APIRouter(tags=["organizador"])
solo_organizador = require_roles("organizador")


@router.get("/organizador/eventos", response_model=list[EventoOrgOut])
def mis_eventos(user: dict = Depends(solo_organizador)):
    return organizador.listar(user["id"])


@router.post("/organizador/eventos", response_model=EventoOrgOut, status_code=201)
def crear(data: EventoIn, user: dict = Depends(solo_organizador)):
    return organizador.crear(user["id"], data.model_dump())


@router.get("/organizador/eventos/{evento_id}", response_model=EventoOrgOut)
def detalle(evento_id: int, user: dict = Depends(solo_organizador)):
    return organizador.obtener(evento_id, user["id"])


@router.put("/organizador/eventos/{evento_id}", response_model=EventoOrgOut)
def editar(evento_id: int, data: EventoIn, user: dict = Depends(solo_organizador)):
    return organizador.editar(evento_id, user["id"], data.model_dump())


@router.post("/organizador/eventos/{evento_id}/estado", response_model=EventoOrgOut)
def estado(evento_id: int, data: EstadoIn, user: dict = Depends(solo_organizador)):
    return organizador.actualizar_estado(evento_id, user["id"], data.estado)


@router.post("/organizador/eventos/{evento_id}/imagen", response_model=EventoOrgOut)
async def subir_imagen(evento_id: int, archivo: UploadFile = File(...), user: dict = Depends(solo_organizador)):
    organizador.obtener(evento_id, user["id"])  # verifica que el evento sea suyo antes de procesar
    clave = imagenes.procesar(evento_id, await archivo.read())
    anterior = organizador.guardar_imagen(evento_id, user["id"], clave)
    imagenes.borrar(anterior)
    return organizador.obtener(evento_id, user["id"])


@router.post("/organizador/eventos/{evento_id}/sectores", response_model=EventoOrgOut, status_code=201)
def agregar_sector(evento_id: int, data: SectorIn, user: dict = Depends(solo_organizador)):
    return organizador.agregar_sector(evento_id, user["id"], data.model_dump())


@router.put("/organizador/sectores/{sector_id}", response_model=EventoOrgOut)
def editar_sector(sector_id: int, data: SectorIn, user: dict = Depends(solo_organizador)):
    return organizador.editar_sector(sector_id, user["id"], data.model_dump())


@router.delete("/organizador/sectores/{sector_id}", response_model=EventoOrgOut)
def eliminar_sector(sector_id: int, user: dict = Depends(solo_organizador)):
    return organizador.eliminar_sector(sector_id, user["id"])


# Imágenes: públicas (se muestran en la cartelera)
@router.get("/imagenes/{archivo}", include_in_schema=False)
def imagen(archivo: str):
    return FileResponse(imagenes.ruta(archivo), media_type="image/webp",
                        headers={"Cache-Control": "public, max-age=86400"})
