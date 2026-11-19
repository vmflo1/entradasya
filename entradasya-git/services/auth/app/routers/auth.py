from fastapi import APIRouter, Depends, status

from app.core.security import create_token, get_current_user
from app.schemas.auth import LoginIn, RegistroIn, TokenOut, UsuarioOut
from app.services import usuarios

router = APIRouter(tags=["auth"])


@router.post("/registro", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def registro(data: RegistroIn):
    """Registro público: siempre crea usuarios con rol cliente."""
    usuario = usuarios.crear_usuario(data.nombre, data.email, data.password, "cliente")
    return TokenOut(access_token=create_token(usuario), usuario=UsuarioOut(**usuario))


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn):
    usuario = usuarios.autenticar(data.email, data.password)
    return TokenOut(access_token=create_token(usuario), usuario=UsuarioOut(**usuario))


@router.get("/me", response_model=UsuarioOut)
def me(user: dict = Depends(get_current_user)):
    return UsuarioOut(**user)
