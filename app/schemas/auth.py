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
    apellido: Optional[str] = Field(None, max_length=100)
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
    apellido: Optional[str] = None
    telefono: Optional[str] = None
    tipo_usuario: TipoUsuario


# Token
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    usuario_id: Optional[int] = None
    email: Optional[str] = None
    tipo_usuario: Optional[TipoUsuario] = None
    
# ============================================
# GOOGLE OAUTH SCHEMAS (Flujo de autorización)
# ============================================

class GoogleAuthURL(BaseModel):
    """Response con URL de autorización de Google"""
    authorization_url: str = Field(..., description="URL para iniciar OAuth con Google")
    message: str = "Redirige al usuario a esta URL"


class GoogleCallbackRequest(BaseModel):
    """Request del callback de Google"""
    code: str = Field(..., description="Authorization code de Google")
    state: Optional[str] = Field(None, description="State para validación")


class GoogleAuthResponse(BaseModel):
    """Response exitoso de Google OAuth"""
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResponse
    es_nuevo_usuario: bool = Field(
        ..., 
        description="True si es primera vez que se loguea con Google"
    )
    
    class Config:
        from_attributes = True