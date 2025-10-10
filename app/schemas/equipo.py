# app/schemas/equipo.py

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional
from enum import Enum

# =============================================
# ENUMS
# =============================================
class RolEmpresa(str, Enum):
    """Roles válidos que pueden asignarse en una empresa"""
    EMPLEADO = "EMPLEADO"
    RECEPCIONISTA = "RECEPCIONISTA"
    ADMIN_EMPRESA = "ADMIN_EMPRESA"
    # EMPRESA no se incluye porque no se puede asignar


# =============================================
# SCHEMAS DE REQUEST
# =============================================
class InvitacionCreate(BaseModel):
    """Schema para invitar un nuevo miembro"""
    email: EmailStr = Field(..., description="Email del usuario a invitar")
    rol: RolEmpresa = Field(..., description="Rol a asignar")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "empleado@empresa.com",
                "rol": "EMPLEADO", # O "RECEPCIONISTA" o "ADMIN_EMPRESA"
            }
        }


class CambiarRolRequest(BaseModel):
    """Schema para cambiar el rol de un miembro"""
    nuevo_rol: RolEmpresa = Field(..., description="Nuevo rol a asignar")
    motivo: Optional[str] = Field(None, max_length=255, description="Motivo del cambio")
    
    class Config:
        json_schema_extra = {
            "example": {
                "nuevo_rol": "ADMIN_EMPRESA",
                "motivo": "Promoción por buen desempeño"
            }
        }


class DesactivarMiembroRequest(BaseModel):
    """Schema para desactivar un miembro"""
    motivo: str = Field(..., min_length=5, max_length=500, description="Motivo de la desactivación")
    
    class Config:
        json_schema_extra = {
            "example": {
                "motivo": "Renuncia voluntaria - último día 15/11/2025"
            }
        }


# =============================================
# SCHEMAS DE RESPONSE
# =============================================
class InvitacionResponse(BaseModel):
    """Respuesta al crear una invitación"""
    message: str
    email: str
    rol: str
    empresa_id: int
    token_invitacion: str = Field(..., description="Token único para aceptar la invitación")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Invitación enviada a empleado@empresa.com",
                "email": "empleado@empresa.com",
                "rol": "EMPLEADO",
                "empresa_id": 1,
                "token_invitacion": "inv_abc123xyz..."
            }
        }


class EquipoMiembro(BaseModel):
    """Información de un miembro del equipo"""
    usuario_id: int
    nombre: str
    email: str
    rol: str = Field(..., description="Nombre del rol")
    rol_id: int
    activo: bool
    fecha_asignado: Optional[datetime] = None
    fecha_desactivacion: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "usuario_id": 5,
                "nombre": "Juan Pérez",
                "email": "juan@empresa.com",
                "rol": "EMPLEADO",
                "rol_id": 5,
                "activo": True,
                "fecha_asignado": "2025-01-15T10:30:00",
                "fecha_desactivacion": None
            }
        }


class EquipoListResponse(BaseModel):
    """Lista completa del equipo de una empresa"""
    total: int = Field(..., description="Total de miembros (activos e inactivos)")
    activos: int = Field(..., description="Total de miembros activos")
    equipo: list[EquipoMiembro]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 5,
                "activos": 4,
                "equipo": [
                    {
                        "usuario_id": 5,
                        "nombre": "Juan Pérez",
                        "email": "juan@empresa.com",
                        "rol": "EMPLEADO",
                        "rol_id": 5,
                        "activo": True,
                        "fecha_asignado": "2025-01-15T10:30:00"
                    }
                ]
            }
        }


class CambioRolResponse(BaseModel):
    """Respuesta al cambiar rol de un miembro"""
    message: str
    usuario_id: int
    rol_anterior: str
    rol_nuevo: str
    fecha_cambio: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Rol cambiado exitosamente",
                "usuario_id": 5,
                "rol_anterior": "EMPLEADO",
                "rol_nuevo": "ADMIN_EMPRESA",
                "fecha_cambio": "2025-10-10T15:30:00"
            }
        }


class DesactivacionResponse(BaseModel):
    """Respuesta al desactivar/reactivar un miembro"""
    message: str
    usuario_id: int
    activo: bool
    fecha_cambio: datetime
    motivo: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Miembro desactivado exitosamente",
                "usuario_id": 5,
                "activo": False,
                "fecha_cambio": "2025-10-10T15:30:00",
                "motivo": "Renuncia voluntaria"
            }
        }