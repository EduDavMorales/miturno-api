from pydantic import BaseModel, Field, validator
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
    id_token: str = Field(..., description="ID token de Google")
    tipo_usuario: str = Field(
        ..., 
        pattern="^(cliente|empresa)$",
        description="Tipo de usuario: 'cliente' o 'empresa'"
    )
    
    @validator('tipo_usuario')
    def validar_tipo(cls, v):
        v = v.lower()
        if v not in ['cliente', 'empresa']:
            raise ValueError('tipo_usuario debe ser "cliente" o "empresa"')
        return v

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
        
# Refresh Token Schemas
class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token para obtener nuevo access token")


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: str  # Devolver el mismo refresh token


class LoginResponseWithRefresh(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    usuario: UsuarioResponse
    
# ============================================
# PASSWORD RESET SCHEMAS
# ============================================

class ForgotPasswordRequest(BaseModel):
    """Request para solicitar recuperación de contraseña"""
    email: str = Field(..., description="Email del usuario")


class ForgotPasswordResponse(BaseModel):
    """Response de solicitud de recuperación"""
    message: str = "Si el email existe, recibirás un correo con instrucciones"
    email: str


class ResetPasswordRequest(BaseModel):
    """Request para resetear contraseña con token"""
    token: str = Field(..., description="Token de recuperación recibido por email")
    nueva_password: str = Field(..., min_length=8, max_length=50, description="Nueva contraseña")
    
    @validator('nueva_password')
    def validar_password_segura(cls, v):
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        if not any(c.isupper() for c in v):
            raise ValueError('La contraseña debe tener al menos una mayúscula')
        if not any(c.islower() for c in v):
            raise ValueError('La contraseña debe tener al menos una minúscula')
        if not any(c.isdigit() for c in v):
            raise ValueError('La contraseña debe tener al menos un número')
        return v


class ResetPasswordResponse(BaseModel):
    """Response de reset exitoso"""
    message: str = "Contraseña actualizada exitosamente"
    email: str