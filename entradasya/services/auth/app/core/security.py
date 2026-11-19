"""Seguridad del servicio auth: cifrado de contraseñas, emisión y validación del JWT."""
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_token(usuario: dict) -> str:
    """El token lleva id y rol (requerimiento), más correo y nombre para que
    orders pueda pedir el envío del correo sin consultar a auth."""
    ahora = datetime.now(timezone.utc)
    payload = {
        "sub": str(usuario["id"]),
        "rol": usuario["rol"],
        "email": usuario["email"],
        "nombre": usuario["nombre"],
        "iat": ahora,
        "exp": ahora + timedelta(minutes=settings.jwt_expires_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(cred: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Falta el token de acceso")
    try:
        payload = jwt.decode(cred.credentials, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "La sesión expiró, vuelve a ingresar")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token inválido")
    return {
        "id": int(payload["sub"]),
        "rol": payload.get("rol"),
        "email": payload.get("email"),
        "nombre": payload.get("nombre"),
    }
