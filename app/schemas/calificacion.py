from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional

# ==================== REQUEST SCHEMAS ====================

class CalificacionCreate(BaseModel):
    """Schema para crear una calificación"""
    turno_id: int = Field(..., description="ID del turno a calificar")
    puntuacion: int = Field(..., ge=1, le=5, description="Puntuación de 1 a 5")
    comentario: Optional[str] = Field(None, max_length=1000, description="Comentario opcional")
    
    @field_validator('comentario')
    @classmethod
    def validar_comentario(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v


class RespuestaEmpresaCreate(BaseModel):
    """Schema para que la empresa responda una calificación"""
    respuesta_empresa: str = Field(..., min_length=1, max_length=1000, description="Respuesta de la empresa")
    
    @field_validator('respuesta_empresa')
    @classmethod
    def validar_respuesta(cls, v):
        return v.strip()


# ==================== RESPONSE SCHEMAS ====================

class CalificacionResponse(BaseModel):
    """Schema de respuesta completa de calificación"""
    calificacion_id: int
    turno_id: int
    cliente_id: int
    empresa_id: int
    puntuacion: int
    comentario: Optional[str] = None
    respuesta_empresa: Optional[str] = None
    fecha_calificacion: datetime
    fecha_respuesta: Optional[datetime] = None
    
    # Datos adicionales del cliente (para mostrar en lista de calificaciones)
    cliente_nombre: Optional[str] = None
    
    class Config:
        from_attributes = True


class CalificacionListResponse(BaseModel):
    """Schema para listar calificaciones (versión simplificada)"""
    calificacion_id: int
    puntuacion: int
    comentario: Optional[str] = None
    respuesta_empresa: Optional[str] = None
    fecha_calificacion: datetime
    fecha_respuesta: Optional[datetime] = None
    cliente_nombre: str
    
    class Config:
        from_attributes = True


class EstadisticasCalificaciones(BaseModel):
    """Schema para estadísticas de calificaciones de una empresa"""
    rating_promedio: Optional[float] = None
    total_calificaciones: int
    distribucion: dict = Field(
        default_factory=dict,
        description="Distribución de calificaciones por estrellas {1: cantidad, 2: cantidad, ...}"
    )
    
    class Config:
        from_attributes = True


class CalificacionCreateResponse(BaseModel):
    """Schema de respuesta al crear una calificación"""
    message: str
    calificacion: CalificacionResponse
    rating_actualizado: Optional[float] = None