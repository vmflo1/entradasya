"""Validación del JWT emitido por auth.

El servicio valida el token por su cuenta con el secreto compartido,
sin llamar a auth en cada petición (requerimiento de auth).
"""
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

bearer = HTTPBearer(auto_error=False)


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
        "token": cred.credentials,
    }


def require_roles(*roles: str):
    """Dependencia que exige que el usuario tenga uno de los roles indicados."""

    def _check(user: dict = Depends(get_current_user)) -> dict:
        if user["rol"] not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "No tienes permiso para esta acción")
        return user

    return _check
