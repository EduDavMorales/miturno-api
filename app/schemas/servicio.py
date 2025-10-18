from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# ==================== REQUEST SCHEMAS ====================

class ServicioCreate(BaseModel):
    """Schema para crear un servicio"""
    nombre: str = Field(..., min_length=3, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)
    precio: float = Field(..., gt=0, description="Precio debe ser mayor a 0")
    duracion_minutos: int = Field(..., gt=0, le=480, description="Duración entre 1 y 480 minutos")
    activo: bool = Field(default=True)


class ServicioUpdate(BaseModel):
    """Schema para actualizar un servicio"""
    nombre: Optional[str] = Field(None, min_length=3, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)
    precio: Optional[float] = Field(None, gt=0)
    duracion_minutos: Optional[int] = Field(None, gt=0, le=480)
    activo: Optional[bool] = None


# ==================== RESPONSE SCHEMAS ====================

class ServicioResponse(BaseModel):
    """Schema de respuesta de servicio"""
    servicio_id: int
    empresa_id: int
    nombre: str
    descripcion: Optional[str] = None
    precio: float
    duracion_minutos: int
    activo: bool
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True