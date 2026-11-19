import logging

from fastapi import HTTPException, status
from psycopg.errors import UniqueViolation

from app.core.security import hash_password, verify_password
from app.db.connection import get_conn

log = logging.getLogger(__name__)


def crear_usuario(nombre: str, email: str, password: str, rol: str = "cliente") -> dict:
    try:
        with get_conn() as conn:
            row = conn.execute(
                """
                INSERT INTO usuarios (nombre, email, password_hash, rol)
                VALUES (%s, %s, %s, %s)
                RETURNING id, nombre, email, rol
                """,
                (nombre, email, hash_password(password), rol),
            ).fetchone()
    except UniqueViolation:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ese correo ya está registrado")
    log.info("Usuario registrado id=%s rol=%s", row["id"], row["rol"])
    return row


def autenticar(email: str, password: str) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, nombre, email, rol, password_hash FROM usuarios WHERE email = %s",
            (email,),
        ).fetchone()
    if row is None or not verify_password(password, row["password_hash"]):
        log.info("Inicio de sesión fallido para %s", email)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Correo o contraseña incorrectos")
    row.pop("password_hash")
    log.info("Inicio de sesión id=%s", row["id"])
    return row
