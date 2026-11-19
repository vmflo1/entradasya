"""Llamadas HTTP/JSON a los otros servicios. Todas tienen tiempo máximo de espera."""
import logging

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)


class ServicioError(Exception):
    """El otro servicio no respondió, tardó demasiado o devolvió un error inesperado."""

    def __init__(self, servicio: str, mensaje: str):
        super().__init__(f"{servicio}: {mensaje}")
        self.servicio = servicio
        self.mensaje = mensaje


class Agotado(Exception):
    pass


def _post(servicio: str, url: str, json: dict, headers: dict) -> httpx.Response:
    try:
        return httpx.post(url, json=json, headers=headers, timeout=settings.http_timeout)
    except httpx.TimeoutException:
        log.error("%s no respondió a tiempo (%ss)", servicio, settings.http_timeout)
        raise ServicioError(servicio, "tiempo de espera agotado")
    except httpx.HTTPError as exc:
        log.error("%s no disponible: %s", servicio, exc)
        raise ServicioError(servicio, "servicio no disponible")


def _get(servicio: str, url: str, headers: dict) -> httpx.Response:
    try:
        return httpx.get(url, headers=headers, timeout=settings.http_timeout)
    except httpx.TimeoutException:
        log.error("%s no respondió a tiempo (%ss)", servicio, settings.http_timeout)
        raise ServicioError(servicio, "tiempo de espera agotado")
    except httpx.HTTPError as exc:
        log.error("%s no disponible: %s", servicio, exc)
        raise ServicioError(servicio, "servicio no disponible")


def _detalle(r: httpx.Response) -> str:
    try:
        return str(r.json().get("detail", r.text))
    except ValueError:
        return r.text


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _interno() -> dict:
    return {"X-Internal-Key": settings.internal_api_key}


# ---------- events ----------

def reservar_cupos(token: str, orden_id: str, evento_id: int, sector_id: int, cantidad: int) -> dict:
    r = _post("events", f"{settings.events_url}/reservas",
              {"orden_id": orden_id, "evento_id": evento_id, "sector_id": sector_id, "cantidad": cantidad},
              _bearer(token))
    if r.status_code == 409 and _detalle(r) == "Agotado":
        raise Agotado()
    if r.status_code != 200:
        raise ServicioError("events", _detalle(r))
    return r.json()


def liberar_cupos(token: str, orden_id: str) -> None:
    try:
        r = _post("events", f"{settings.events_url}/reservas/{orden_id}/liberar", {}, _bearer(token))
        if r.status_code != 200:
            log.error("events no pudo liberar los cupos de la orden %s: %s", orden_id, _detalle(r))
    except ServicioError:
        log.error("No se pudieron liberar los cupos de la orden %s", orden_id)


class NoEsDueno(Exception):
    pass


def evento_del_organizador(token: str, evento_id: int) -> dict:
    """Pregunta a events si el evento pertenece al organizador del token."""
    r = _get("events", f"{settings.events_url}/organizador/eventos/{evento_id}", _bearer(token))
    if r.status_code in (403, 404):
        raise NoEsDueno()
    if r.status_code != 200:
        raise ServicioError("events", _detalle(r))
    return r.json()


# ---------- payments ----------

def cobrar(orden_id: str, monto: str, metodo: str, tarjeta_numero: str | None) -> dict:
    # El titular, el vencimiento y el código de seguridad (CVV) no se envían ni se guardan
    r = _post("payments", f"{settings.payments_url}/pagos",
              {"orden_id": orden_id, "monto": monto, "metodo": metodo, "tarjeta_numero": tarjeta_numero},
              _interno())
    if r.status_code != 200:
        raise ServicioError("payments", _detalle(r))
    return r.json()


# ---------- tickets ----------

def generar_entradas(token: str, datos: dict) -> list[dict]:
    r = _post("tickets", f"{settings.tickets_url}/entradas/generar", datos, _bearer(token))
    if r.status_code != 200:
        raise ServicioError("tickets", _detalle(r))
    return r.json()


# ---------- notifications ----------

def enviar_confirmacion(datos: dict) -> None:
    r = _post("notifications", f"{settings.notifications_url}/correos/confirmacion", datos, _interno())
    if r.status_code != 200:
        raise ServicioError("notifications", _detalle(r))
