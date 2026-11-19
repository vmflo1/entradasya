"""Control de ingreso: cada entrada sirve una sola vez."""
import logging

from fastapi import HTTPException, status

from app.db.connection import get_conn
from app.services import clientes

log = logging.getLogger(__name__)


def _asistentes(conn, evento_id: int) -> int:
    return conn.execute("SELECT COUNT(*) AS n FROM ingresos WHERE evento_id = %s", (evento_id,)).fetchone()["n"]


def _rechazar(user: dict, codigo: str, evento_id: int, motivo: str, **extra) -> dict:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO rechazos (codigo, evento_id, motivo, portero_id) VALUES (%s, %s, %s, %s)",
            (codigo, evento_id, motivo, user["id"]),
        )
        total = _asistentes(conn, evento_id)
    log.info("Ingreso RECHAZADO: codigo=%s evento=%s motivo=%s", codigo, evento_id, motivo)
    return {"permitido": False, "codigo": codigo, "motivo": motivo, "asistentes": total, **extra}


def registrar(user: dict, codigo: str, evento_id: int) -> dict:
    # 1. tickets dice si el código existe, si es de este evento y si es válido
    try:
        v = clientes.validar_codigo(user["token"], codigo, evento_id)
    except clientes.ServicioError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, f"No se pudo validar la entrada: {exc.mensaje}")

    if not v["existe"]:
        return _rechazar(user, codigo, evento_id, "Código inválido")
    if not v["pertenece_al_evento"]:
        return _rechazar(user, codigo, evento_id, "Entrada de otro evento", evento_nombre=v.get("evento_nombre"))
    if not v["valida"]:
        return _rechazar(user, codigo, evento_id, v.get("motivo") or "Entrada no válida",
                         evento_nombre=v.get("evento_nombre"))

    # 2. Registrar el ingreso. La restricción UNIQUE(codigo) garantiza un solo ingreso,
    #    incluso si dos porteros escanean la misma entrada al mismo tiempo.
    with get_conn() as conn:
        nuevo = conn.execute(
            """
            INSERT INTO ingresos (codigo, evento_id, evento_nombre, sector_nombre, portero_id, portero_nombre)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (codigo) DO NOTHING
            RETURNING ingresado_en
            """,
            (codigo, evento_id, v.get("evento_nombre"), v.get("sector_nombre"), user["id"], user.get("nombre")),
        ).fetchone()
        if nuevo is None:
            primero = conn.execute(
                "SELECT ingresado_en FROM ingresos WHERE codigo = %s", (codigo,)
            ).fetchone()["ingresado_en"]
        total = _asistentes(conn, evento_id)

    if nuevo is None:
        return _rechazar(user, codigo, evento_id,
                         f"Entrada ya utilizada (primer ingreso: {primero:%d/%m/%Y %H:%M:%S})",
                         evento_nombre=v.get("evento_nombre"), primer_ingreso=primero)

    log.info("Ingreso PERMITIDO: codigo=%s evento=%s portero=%s", codigo, evento_id, user["id"])
    return {"permitido": True, "codigo": codigo, "evento_nombre": v.get("evento_nombre"),
            "sector_nombre": v.get("sector_nombre"), "ingresado_en": nuevo["ingresado_en"], "asistentes": total}


def contar(evento_id: int) -> dict:
    with get_conn() as conn:
        rechazos = conn.execute(
            "SELECT COUNT(*) AS n FROM rechazos WHERE evento_id = %s", (evento_id,)
        ).fetchone()["n"]
        por_sector = conn.execute(
            """
            SELECT COALESCE(sector_nombre, 'Sin zona') AS sector, COUNT(*)::int AS ingresados
            FROM ingresos WHERE evento_id = %s
            GROUP BY 1 ORDER BY 1
            """,
            (evento_id,),
        ).fetchall()
        return {"evento_id": evento_id, "asistentes": _asistentes(conn, evento_id),
                "rechazos": rechazos, "por_sector": por_sector}
