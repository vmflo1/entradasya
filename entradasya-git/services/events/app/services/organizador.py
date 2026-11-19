"""Gestión de eventos por parte del organizador.

Cada organizador ve y modifica sus propios eventos y, además, los eventos cargados en el
sistema sin organizador asignado (los datos de prueba de 002_datos_prueba.sql).
Los eventos de otro organizador nunca se ven ni se modifican."""
import logging

from fastapi import HTTPException, status

from app.db.connection import get_conn

log = logging.getLogger(__name__)

# Transiciones de estado permitidas
TRANSICIONES = {
    "borrador": {"publicado", "cancelado"},
    "publicado": {"borrador", "cancelado"},
    "cancelado": set(),
}


def _sectores(conn, evento_id: int) -> list[dict]:
    filas = conn.execute(
        """
        SELECT id, nombre, precio, cupo_total, cupo_disponible,
               cupo_total - cupo_disponible AS vendidos
        FROM sectores WHERE evento_id = %s ORDER BY precio DESC, id
        """,
        (evento_id,),
    ).fetchall()
    return filas


def _completar(conn, evento: dict) -> dict:
    sectores = _sectores(conn, evento["id"])
    evento["sectores"] = sectores
    evento["cupo_total"] = sum(s["cupo_total"] for s in sectores)
    evento["vendidos"] = sum(s["vendidos"] for s in sectores)
    return evento


def _propio(conn, evento_id: int, organizador_id: int) -> dict:
    evento = conn.execute(
        """
        SELECT id, nombre, fecha, lugar, imagen, descripcion, estado
        FROM eventos WHERE id = %s AND (organizador_id = %s OR organizador_id IS NULL)
        """,
        (evento_id, organizador_id),
    ).fetchone()
    if evento is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Evento no encontrado")
    return evento


def listar(organizador_id: int) -> list[dict]:
    with get_conn() as conn:
        eventos = conn.execute(
            """
            SELECT id, nombre, fecha, lugar, imagen, descripcion, estado
            FROM eventos WHERE organizador_id = %s OR organizador_id IS NULL ORDER BY fecha
            """,
            (organizador_id,),
        ).fetchall()
        return [_completar(conn, e) for e in eventos]


def obtener(evento_id: int, organizador_id: int) -> dict:
    with get_conn() as conn:
        return _completar(conn, _propio(conn, evento_id, organizador_id))


def crear(organizador_id: int, datos: dict) -> dict:
    """Los eventos nuevos nacen en borrador: no aparecen en la cartelera hasta publicarlos."""
    with get_conn() as conn:
        evento = conn.execute(
            """
            INSERT INTO eventos (nombre, fecha, lugar, descripcion, estado, organizador_id)
            VALUES (%s, %s, %s, %s, 'borrador', %s)
            RETURNING id, nombre, fecha, lugar, imagen, descripcion, estado
            """,
            (datos["nombre"], datos["fecha"], datos["lugar"], datos["descripcion"], organizador_id),
        ).fetchone()
        log.info("Evento %s creado por el organizador %s", evento["id"], organizador_id)
        return _completar(conn, evento)


def editar(evento_id: int, organizador_id: int, datos: dict) -> dict:
    with get_conn() as conn:
        evento = _propio(conn, evento_id, organizador_id)
        if evento["estado"] == "cancelado":
            raise HTTPException(status.HTTP_409_CONFLICT, "Un evento cancelado no se puede editar")
        evento = conn.execute(
            """
            UPDATE eventos SET nombre = %s, fecha = %s, lugar = %s, descripcion = %s
            WHERE id = %s
            RETURNING id, nombre, fecha, lugar, imagen, descripcion, estado
            """,
            (datos["nombre"], datos["fecha"], datos["lugar"], datos["descripcion"], evento_id),
        ).fetchone()
        return _completar(conn, evento)


def actualizar_estado(evento_id: int, organizador_id: int, nuevo: str) -> dict:
    with get_conn() as conn:
        evento = _propio(conn, evento_id, organizador_id)
        actual = evento["estado"]
        if nuevo == actual:
            return _completar(conn, evento)
        if nuevo not in TRANSICIONES[actual]:
            raise HTTPException(status.HTTP_409_CONFLICT, f"No se puede pasar de {actual} a {nuevo}")
        sectores = _sectores(conn, evento_id)
        if nuevo == "publicado" and not sectores:
            raise HTTPException(status.HTTP_409_CONFLICT, "Agrega al menos un sector antes de publicar")
        if nuevo == "borrador" and any(s["vendidos"] > 0 for s in sectores):
            raise HTTPException(status.HTTP_409_CONFLICT, "El evento ya tiene ventas: no puede volver a borrador")
        evento = conn.execute(
            """
            UPDATE eventos SET estado = %s WHERE id = %s
            RETURNING id, nombre, fecha, lugar, imagen, descripcion, estado
            """,
            (nuevo, evento_id),
        ).fetchone()
    log.info("Evento %s: %s -> %s", evento_id, actual, nuevo)
    return obtener(evento_id, organizador_id)


def guardar_imagen(evento_id: int, organizador_id: int, clave: str) -> str | None:
    """Guarda la clave de la nueva imagen y devuelve la anterior (para borrar sus archivos)."""
    with get_conn() as conn:
        evento = _propio(conn, evento_id, organizador_id)
        conn.execute("UPDATE eventos SET imagen = %s WHERE id = %s", (clave, evento_id))
    return evento["imagen"]


# ---------- Sectores ----------

def agregar_sector(evento_id: int, organizador_id: int, datos: dict) -> dict:
    with get_conn() as conn:
        evento = _propio(conn, evento_id, organizador_id)
        if evento["estado"] == "cancelado":
            raise HTTPException(status.HTTP_409_CONFLICT, "El evento está cancelado")
        conn.execute(
            """
            INSERT INTO sectores (evento_id, nombre, precio, cupo_total, cupo_disponible)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (evento_id, datos["nombre"], datos["precio"], datos["cupo_total"], datos["cupo_total"]),
        )
    return obtener(evento_id, organizador_id)


def _sector_propio(conn, sector_id: int, organizador_id: int) -> dict:
    sector = conn.execute(
        """
        SELECT s.id, s.evento_id, s.cupo_total, s.cupo_disponible, e.estado
        FROM sectores s JOIN eventos e ON e.id = s.evento_id
        WHERE s.id = %s AND (e.organizador_id = %s OR e.organizador_id IS NULL)
        """,
        (sector_id, organizador_id),
    ).fetchone()
    if sector is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sector no encontrado")
    if sector["estado"] == "cancelado":
        raise HTTPException(status.HTTP_409_CONFLICT, "El evento está cancelado")
    return sector


def editar_sector(sector_id: int, organizador_id: int, datos: dict) -> dict:
    """El cupo total nunca puede quedar por debajo de lo ya vendido o reservado."""
    with get_conn() as conn:
        sector = _sector_propio(conn, sector_id, organizador_id)
        fila = conn.execute(
            """
            UPDATE sectores
            SET nombre = %s, precio = %s, cupo_total = %s,
                cupo_disponible = %s - (cupo_total - cupo_disponible)
            WHERE id = %s AND (cupo_total - cupo_disponible) <= %s
            RETURNING id
            """,
            (datos["nombre"], datos["precio"], datos["cupo_total"], datos["cupo_total"],
             sector_id, datos["cupo_total"]),
        ).fetchone()
        if fila is None:
            vendidos = sector["cupo_total"] - sector["cupo_disponible"]
            raise HTTPException(status.HTTP_409_CONFLICT,
                                f"El cupo no puede ser menor a lo ya vendido ({vendidos})")
    return obtener(sector["evento_id"], organizador_id)


def eliminar_sector(sector_id: int, organizador_id: int) -> dict:
    with get_conn() as conn:
        sector = _sector_propio(conn, sector_id, organizador_id)
        usado = conn.execute("SELECT 1 FROM reservas WHERE sector_id = %s LIMIT 1", (sector_id,)).fetchone()
        if usado or sector["cupo_disponible"] != sector["cupo_total"]:
            raise HTTPException(status.HTTP_409_CONFLICT, "El sector ya tiene ventas: no se puede eliminar")
        conn.execute("DELETE FROM sectores WHERE id = %s", (sector_id,))
    return obtener(sector["evento_id"], organizador_id)
