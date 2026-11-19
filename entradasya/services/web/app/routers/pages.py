"""Sirve las páginas. Los datos los carga el navegador desde /api/... (vía Nginx)."""
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

import time

from app.core.config import SERVICE_DIR, settings

router = APIRouter(include_in_schema=False)

# Versión de los archivos estáticos: cambia cada vez que se reinicia web.
# Se agrega a las URLs (?v=...) para que el navegador no use un JS o CSS viejo guardado en caché.
VERSION_ESTATICOS = str(int(time.time()))
templates = Jinja2Templates(directory=SERVICE_DIR / "templates")


def _page(request: Request, plantilla: str, **contexto):
    respuesta = templates.TemplateResponse(
        request, plantilla, {"app_name": settings.app_name, "v": VERSION_ESTATICOS, **contexto})
    respuesta.headers["Cache-Control"] = "no-cache"
    return respuesta


@router.get("/")
def cartelera(request: Request):
    return _page(request, "cliente/cartelera.html", activo="cartelera")


@router.get("/evento/{evento_id}")
def evento(request: Request, evento_id: int):
    return _page(request, "cliente/evento.html", evento_id=evento_id)


@router.get("/confirmacion/{orden_id}")
def confirmacion(request: Request, orden_id: str):
    return _page(request, "cliente/confirmacion.html", orden_id=orden_id)


@router.get("/mis-entradas")
def mis_entradas(request: Request):
    return _page(request, "cliente/mis_entradas.html", activo="mis-entradas")


@router.get("/login")
def login(request: Request):
    return _page(request, "cliente/login.html")


@router.get("/registro")
def registro(request: Request):
    return _page(request, "cliente/registro.html")


# ---------- Organizador ----------

@router.get("/organizador")
def organizador_panel(request: Request):
    return _page(request, "organizador/panel.html")


@router.get("/organizador/nuevo")
def organizador_nuevo(request: Request):
    return _page(request, "organizador/nuevo.html")


@router.get("/organizador/evento/{evento_id}")
def organizador_evento(request: Request, evento_id: int):
    return _page(request, "organizador/evento.html", evento_id=evento_id)


# ---------- Portero ----------

@router.get("/portero")
def portero_eventos(request: Request):
    return _page(request, "portero/eventos.html")


@router.get("/portero/evento/{evento_id}")
def portero_control(request: Request, evento_id: int):
    return _page(request, "portero/control.html", evento_id=evento_id)
