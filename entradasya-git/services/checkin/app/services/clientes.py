"""Llamada HTTP/JSON a tickets, con tiempo máximo de espera."""
import logging

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)


class ServicioError(Exception):
    def __init__(self, servicio: str, mensaje: str):
        super().__init__(f"{servicio}: {mensaje}")
        self.mensaje = mensaje


def validar_codigo(token: str, codigo: str, evento_id: int) -> dict:
    """Pregunta a tickets si el código existe, a qué evento pertenece y si es válido."""
    try:
        r = httpx.get(
            f"{settings.tickets_url}/entradas/{codigo}/validar",
            params={"evento_id": evento_id},
            headers={"Authorization": f"Bearer {token}"},
            timeout=settings.http_timeout,
        )
    except httpx.TimeoutException:
        log.error("tickets no respondió a tiempo (%ss)", settings.http_timeout)
        raise ServicioError("tickets", "tiempo de espera agotado")
    except httpx.HTTPError as exc:
        log.error("tickets no disponible: %s", exc)
        raise ServicioError("tickets", "servicio no disponible")
    if r.status_code != 200:
        raise ServicioError("tickets", f"respuesta inesperada ({r.status_code})")
    return r.json()
