"""Herramienta de administración: crea usuarios con rol organizador o portero.

El registro público de la web siempre crea clientes. Los organizadores y porteros
los crea un administrador desde la carpeta del servicio auth:

  Windows:  .\\.venv\\Scripts\\python.exe -m app.cli --nombre "Olga Organizadora" --email organizador@prueba.com --password clave123 --rol organizador
  Linux:    .venv/bin/python -m app.cli --nombre "Pedro Portero" --email portero@prueba.com --password clave123 --rol portero

Si el correo ya existe, actualiza su rol (y su contraseña).
"""
import argparse
import sys

from app.core.logging import setup_logging
from app.core.security import hash_password
from app.db.connection import get_conn, run_migrations

ROLES = ("cliente", "organizador", "portero")


def main() -> int:
    parser = argparse.ArgumentParser(description="Crear o actualizar un usuario con rol")
    parser.add_argument("--nombre", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--rol", required=True, choices=ROLES)
    args = parser.parse_args()

    email = args.email.strip().lower()
    if len(args.password) < 6 or len(args.password.encode("utf-8")) > 72:
        print("La contraseña debe tener entre 6 y 72 caracteres.")
        return 1

    setup_logging("WARNING")
    run_migrations()
    with get_conn() as conn:
        fila = conn.execute(
            """
            INSERT INTO usuarios (nombre, email, password_hash, rol)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email) DO UPDATE
                SET nombre = EXCLUDED.nombre, password_hash = EXCLUDED.password_hash, rol = EXCLUDED.rol
            RETURNING id, nombre, email, rol
            """,
            (args.nombre.strip(), email, hash_password(args.password), args.rol),
        ).fetchone()
    print(f"Usuario listo: id={fila['id']}  {fila['nombre']} <{fila['email']}>  rol={fila['rol']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
