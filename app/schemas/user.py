from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Literal
from datetime import datetime
from app.models.user import TipoUsuario


# Schema base
class UsuarioBase(BaseModel):
    email: EmailStr
    nombre: str
    telefono: str
    tipo_usuario: TipoUsuario


# Schema para crear usuario
class UsuarioCreate(UsuarioBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('La contraseña debe tener al menos 6 caracteres')
        return v
    
    @validator('telefono')
    def validate_telefono(cls, v):
        # Remover espacios y guiones
        v = v.replace(' ', '').replace('-', '')
        if not v.isdigit() or len(v) < 10:
            raise ValueError('El teléfono debe tener al menos 10 dígitos')
        return v


# Schema para actualizar usuario
class UsuarioUpdate(BaseModel):
    email: Optional[EmailStr] = None
    nombre: Optional[str] = None
    telefono: Optional[str] = None
    
    @validator('telefono')
    def validate_telefono(cls, v):
        if v is not None:
            v = v.replace(' ', '').replace('-', '')
            if not v.isdigit() or len(v) < 10:
                raise ValueError('El teléfono debe tener al menos 10 dígitos')
        return v


# Schema para respuesta (sin password)
class UsuarioResponse(UsuarioBase):
    usuario_id: int
    fecha_creacion: datetime
    fecha_actualizacion: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Schema para login
class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str


# Schema para cambiar contraseña
class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('La nueva contraseña debe tener al menos 6 caracteres')
        return v


# Schema para respuesta de login
class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResponse


# Schema para verificar token
class TokenData(BaseModel):
    email: Optional[str] = None


# Schemas específicos por tipo de usuario
class ClienteResponse(UsuarioResponse):
    """Respuesta específica para clientes"""
    # Aquí puedes agregar campos específicos de clientes si los necesitas
    pass


class EmpresaUsuarioResponse(UsuarioResponse):
    """Respuesta específica para usuarios empresa"""
    # Aquí puedes agregar campos específicos de empresas si los necesitas
    pass


# Schema para listado con paginación
class UsuariosListResponse(BaseModel):
    usuarios: list[UsuarioResponse]
    total: int
    skip: int
    limit: int