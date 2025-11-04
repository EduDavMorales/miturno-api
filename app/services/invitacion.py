"""
Schemas Pydantic para el sistema de invitaciones
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum


class EstadoInvitacion(str, Enum):
    """Estados posibles de una invitación"""
    PENDIENTE = "pendiente"
    ACEPTADA = "aceptada"
    RECHAZADA = "rechazada"
    EXPIRADA = "expirada"


class RolInvitacion(str, Enum):
    """Roles que se pueden asignar vía invitación"""
    EMPLEADO = "EMPLEADO"
    RECEPCIONISTA = "RECEPCIONISTA"
    ADMIN_EMPRESA = "ADMIN_EMPRESA"


class InvitacionCreate(BaseModel):
    """Schema para crear una nueva invitación"""
    email: EmailStr = Field(..., description="Email del invitado")
    rol: RolInvitacion = Field(..., description="Rol a asignar")
    mensaje_personalizado: Optional[str] = Field(
        None, 
        max_length=500,
        description="Mensaje opcional del invitante"
    )
    
    @validator('email')
    def email_valido(cls, v):
        """Valida formato de email"""
        if not v or '@' not in v:
            raise ValueError('Email inválido')
        return v.lower().strip()
    
    @validator('mensaje_personalizado')
    def mensaje_valido(cls, v):
        """Valida mensaje personalizado"""
        if v:
            v = v.strip()
            if len(v) < 10:
                raise ValueError('El mensaje debe tener al menos 10 caracteres')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "email": "empleado@empresa.com",
                "rol": "EMPLEADO",
                "mensaje_personalizado": "¡Bienvenido al equipo! Estamos emocionados de trabajar contigo."
            }
        }


class InvitacionResponse(BaseModel):
    """Schema de respuesta al crear invitación"""
    message: str
    invitacion_id: int
    email: str
    empresa_id: int
    rol: str
    token_invitacion: str
    email_enviado: bool
    fecha_expiracion: datetime
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "message": "Invitación enviada a empleado@empresa.com",
                "invitacion_id": 15,
                "email": "empleado@empresa.com",
                "empresa_id": 1,
                "rol": "EMPLEADO",
                "token_invitacion": "inv_abc123xyz789",
                "email_enviado": True,
                "fecha_expiracion": "2025-10-28T10:00:00"
            }
        }


class InvitacionDetalle(BaseModel):
    """Schema detallado de una invitación"""
    invitacion_id: int
    empresa_id: int
    empresa_nombre: str
    email: str
    rol_nombre: str
    estado: EstadoInvitacion
    fecha_creacion: datetime
    fecha_expiracion: datetime
    fecha_aceptacion: Optional[datetime] = None
    invitado_por_nombre: str
    mensaje_personalizado: Optional[str] = None
    
    class Config:
        orm_mode = True


class InvitacionValidar(BaseModel):
    """Schema para validar un token de invitación"""
    token: str = Field(..., min_length=10, description="Token de invitación")
    
    class Config:
        schema_extra = {
            "example": {
                "token": "inv_abc123xyz789def456"
            }
        }


class InvitacionValidarResponse(BaseModel):
    """Schema de respuesta al validar token"""
    valido: bool
    mensaje: str
    invitacion: Optional[InvitacionDetalle] = None
    
    class Config:
        schema_extra = {
            "example": {
                "valido": True,
                "mensaje": "Invitación válida",
                "invitacion": {
                    "invitacion_id": 15,
                    "empresa_id": 1,
                    "empresa_nombre": "Barbería Central",
                    "email": "empleado@empresa.com",
                    "rol_nombre": "EMPLEADO",
                    "estado": "pendiente",
                    "fecha_creacion": "2025-10-21T10:00:00",
                    "fecha_expiracion": "2025-10-28T10:00:00",
                    "invitado_por_nombre": "Juan Pérez"
                }
            }
        }


class InvitacionAceptar(BaseModel):
    """Schema para aceptar una invitación"""
    token: str = Field(..., min_length=10)
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=8, description="Contraseña del nuevo usuario")
    telefono: Optional[str] = Field(None, min_length=10, max_length=20)
    
    @validator('password')
    def password_fuerte(cls, v):
        """Valida que la contraseña sea fuerte"""
        if len(v) < 8:
            raise ValueError('La contraseña debe tener al menos 8 caracteres')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "token": "inv_abc123xyz789def456",
                "nombre": "Juan",
                "apellido": "Pérez",
                "password": "MiPassword123",
                "telefono": "+541123456789"
            }
        }


class InvitacionAceptarResponse(BaseModel):
    """Schema de respuesta al aceptar invitación"""
    message: str
    usuario_id: int
    email: str
    empresa_id: int
    rol_asignado: str
    access_token: str
    refresh_token: str
    
    class Config:
        schema_extra = {
            "example": {
                "message": "Invitación aceptada exitosamente. ¡Bienvenido al equipo!",
                "usuario_id": 25,
                "email": "empleado@empresa.com",
                "empresa_id": 1,
                "rol_asignado": "EMPLEADO",
                "access_token": "eyJhbGc...",
                "refresh_token": "eyJhbGc..."
            }
        }


class InvitacionListar(BaseModel):
    """Schema para listar invitaciones de una empresa"""
    invitaciones: list[InvitacionDetalle]
    total: int
    pendientes: int
    aceptadas: int
    expiradas: int
    
    class Config:
        schema_extra = {
            "example": {
                "invitaciones": [],
                "total": 10,
                "pendientes": 3,
                "aceptadas": 6,
                "expiradas": 1
            }
        }


class InvitacionReenviar(BaseModel):
    """Schema para reenviar una invitación"""
    invitacion_id: int
    mensaje_personalizado: Optional[str] = Field(None, max_length=500)
    
    class Config:
        schema_extra = {
            "example": {
                "invitacion_id": 15,
                "mensaje_personalizado": "Te reenvío la invitación, ¡esperamos tu respuesta!"
            }
        }


class InvitacionCancelar(BaseModel):
    """Schema para cancelar una invitación"""
    motivo: Optional[str] = Field(None, max_length=500, description="Motivo de cancelación")
    
    class Config:
        schema_extra = {
            "example": {
                "motivo": "El puesto fue cubierto por otro candidato"
            }
        }