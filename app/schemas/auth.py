from pydantic import BaseModel, Field
from typing import Optional
from app.models.user import TipoUsuario


# Login
class LoginRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8, max_length=50)


class LoginResponse(BaseModel):
    message: str
    token: str
    usuario: "UsuarioResponse"


# Google OAuth
class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., max_length=2000)
    tipo_usuario: TipoUsuario


# Registro
class RegistroRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8, max_length=50)
    nombre: str = Field(..., min_length=2, max_length=100)
    telefono: str = Field(..., min_length=10, max_length=15)
    tipo_usuario: TipoUsuario
    categoria_id: Optional[int] = None


class RegistroResponse(BaseModel):
    message: str
    usuario_id: int


# Usuario Response
class UsuarioResponse(BaseModel):
    class Config:
        from_attributes = True
    
    usuario_id: int
    email: str
    nombre: str
    telefono: str
    tipo_usuario: TipoUsuario


# Token
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    usuario_id: Optional[int] = None
    email: Optional[str] = None
    tipo_usuario: Optional[TipoUsuario] = None