# app/schemas/horario.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import time, date, datetime
from enum import Enum

# Enums para horarios
class DiaSemanaEnum(str, Enum):
    LUNES = "lunes"
    MARTES = "martes"
    MIERCOLES = "miercoles"
    JUEVES = "jueves"
    VIERNES = "viernes"
    SABADO = "sabado"
    DOMINGO = "domingo"

class TipoBloqueoEnum(str, Enum):
    FERIADO = "FERIADO"
    VACACIONES = "VACACIONES"
    MANTENIMIENTO = "MANTENIMIENTO"
    OTRO = "OTRO"

# ============================================
# SCHEMAS DE HORARIOS
# ============================================

class HorarioCreate(BaseModel):
    """Schema para crear un horario de empresa"""
    empresa_id: int = Field(..., description="ID de la empresa")
    dia_semana: DiaSemanaEnum = Field(..., description="Día de la semana")
    hora_apertura: time = Field(..., description="Hora de apertura (HH:MM:SS)")
    hora_cierre: time = Field(..., description="Hora de cierre (HH:MM:SS)")
    activo: bool = Field(default=True, description="Si el horario está activo")
    
    @validator('hora_cierre')
    def validar_hora_cierre(cls, v, values):
        """Validar que hora_cierre sea posterior a hora_apertura"""
        if 'hora_apertura' in values and v <= values['hora_apertura']:
            raise ValueError('La hora de cierre debe ser posterior a la hora de apertura')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "empresa_id": 1,
                "dia_semana": "lunes",
                "hora_apertura": "09:00:00",
                "hora_cierre": "18:00:00",
                "activo": True
            }
        }


class HorarioUpdate(BaseModel):
    """Schema para actualizar un horario existente"""
    hora_apertura: Optional[time] = Field(None, description="Nueva hora de apertura")
    hora_cierre: Optional[time] = Field(None, description="Nueva hora de cierre")
    activo: Optional[bool] = Field(None, description="Estado del horario")
    
    @validator('hora_cierre')
    def validar_hora_cierre(cls, v, values):
        """Validar que hora_cierre sea posterior a hora_apertura si ambas están presentes"""
        if v is not None and 'hora_apertura' in values and values['hora_apertura'] is not None:
            if v <= values['hora_apertura']:
                raise ValueError('La hora de cierre debe ser posterior a la hora de apertura')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "hora_apertura": "08:00:00",
                "hora_cierre": "20:00:00",
                "activo": True
            }
        }


class HorarioResponse(BaseModel):
    """Schema de respuesta para un horario"""
    horario_id: int
    empresa_id: int
    dia_semana: str
    hora_apertura: time
    hora_cierre: time
    activo: bool
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "horario_id": 1,
                "empresa_id": 1,
                "dia_semana": "lunes",
                "hora_apertura": "09:00:00",
                "hora_cierre": "18:00:00",
                "activo": True
            }
        }


class HorariosListResponse(BaseModel):
    """Schema para listar múltiples horarios"""
    horarios: List[HorarioResponse]
    total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "horarios": [
                    {
                        "horario_id": 1,
                        "empresa_id": 1,
                        "dia_semana": "lunes",
                        "hora_apertura": "09:00:00",
                        "hora_cierre": "18:00:00",
                        "activo": True
                    }
                ],
                "total": 1
            }
        }


class HorarioBulkCreate(BaseModel):
    """Schema para crear múltiples horarios a la vez"""
    empresa_id: int = Field(..., description="ID de la empresa")
    horarios: List[dict] = Field(..., description="Lista de horarios a crear")
    
    class Config:
        json_schema_extra = {
            "example": {
                "empresa_id": 1,
                "horarios": [
                    {"dia_semana": "lunes", "hora_apertura": "09:00:00", "hora_cierre": "18:00:00"},
                    {"dia_semana": "martes", "hora_apertura": "09:00:00", "hora_cierre": "18:00:00"},
                    {"dia_semana": "miercoles", "hora_apertura": "09:00:00", "hora_cierre": "18:00:00"}
                ]
            }
        }


# ============================================
# SCHEMAS DE BLOQUEOS
# ============================================

class BloqueoCreate(BaseModel):
    """Schema para crear un bloqueo de horario"""
    empresa_id: int = Field(..., description="ID de la empresa")
    fecha_inicio: date = Field(..., description="Fecha de inicio del bloqueo")
    fecha_fin: date = Field(..., description="Fecha de fin del bloqueo")
    hora_inicio: Optional[time] = Field(None, description="Hora de inicio (null para día completo)")
    hora_fin: Optional[time] = Field(None, description="Hora de fin (null para día completo)")
    motivo: Optional[str] = Field(None, max_length=255, description="Motivo del bloqueo")
    tipo: TipoBloqueoEnum = Field(default=TipoBloqueoEnum.OTRO, description="Tipo de bloqueo")
    
    @validator('fecha_fin')
    def validar_fecha_fin(cls, v, values):
        """Validar que fecha_fin sea posterior o igual a fecha_inicio"""
        if 'fecha_inicio' in values and v < values['fecha_inicio']:
            raise ValueError('La fecha de fin debe ser posterior o igual a la fecha de inicio')
        return v
    
    @validator('hora_fin')
    def validar_hora_fin(cls, v, values):
        """Validar que si hay hora_fin, debe haber hora_inicio y ser posterior"""
        if v is not None:
            if 'hora_inicio' not in values or values['hora_inicio'] is None:
                raise ValueError('Si especificas hora_fin, debes especificar hora_inicio')
            if v <= values['hora_inicio']:
                raise ValueError('La hora de fin debe ser posterior a la hora de inicio')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "empresa_id": 1,
                "fecha_inicio": "2025-12-25",
                "fecha_fin": "2025-12-25",
                "hora_inicio": None,
                "hora_fin": None,
                "motivo": "Feriado de Navidad",
                "tipo": "FERIADO"
            }
        }


class BloqueoUpdate(BaseModel):
    """Schema para actualizar un bloqueo existente"""
    fecha_inicio: Optional[date] = Field(None, description="Nueva fecha de inicio")
    fecha_fin: Optional[date] = Field(None, description="Nueva fecha de fin")
    hora_inicio: Optional[time] = Field(None, description="Nueva hora de inicio")
    hora_fin: Optional[time] = Field(None, description="Nueva hora de fin")
    motivo: Optional[str] = Field(None, max_length=255, description="Nuevo motivo")
    tipo: Optional[TipoBloqueoEnum] = Field(None, description="Nuevo tipo de bloqueo")
    
    class Config:
        json_schema_extra = {
            "example": {
                "motivo": "Vacaciones extendidas",
                "fecha_fin": "2025-12-31"
            }
        }


class BloqueoResponse(BaseModel):
    """Schema de respuesta para un bloqueo"""
    bloqueo_id: int
    empresa_id: int
    fecha_inicio: date
    fecha_fin: date
    hora_inicio: Optional[time]
    hora_fin: Optional[time]
    motivo: Optional[str]
    tipo: str
    fecha_creacion: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "bloqueo_id": 1,
                "empresa_id": 1,
                "fecha_inicio": "2025-12-25",
                "fecha_fin": "2025-12-25",
                "hora_inicio": None,
                "hora_fin": None,
                "motivo": "Feriado de Navidad",
                "tipo": "FERIADO",
                "fecha_creacion": "2025-10-30T10:00:00"
            }
        }


class BloqueosListResponse(BaseModel):
    """Schema para listar múltiples bloqueos"""
    bloqueos: List[BloqueoResponse]
    total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "bloqueos": [
                    {
                        "bloqueo_id": 1,
                        "empresa_id": 1,
                        "fecha_inicio": "2025-12-25",
                        "fecha_fin": "2025-12-25",
                        "hora_inicio": None,
                        "hora_fin": None,
                        "motivo": "Feriado de Navidad",
                        "tipo": "FERIADO",
                        "fecha_creacion": "2025-10-30T10:00:00"
                    }
                ],
                "total": 1
            }
        }


# ============================================
# SCHEMAS ADICIONALES
# ============================================

class DisponibilidadDia(BaseModel):
    """Schema para representar la disponibilidad de un día específico"""
    fecha: date
    dia_semana: str
    abierto: bool
    horario: Optional[HorarioResponse] = None
    bloqueos: List[BloqueoResponse] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "fecha": "2025-10-30",
                "dia_semana": "jueves",
                "abierto": True,
                "horario": {
                    "horario_id": 1,
                    "empresa_id": 1,
                    "dia_semana": "jueves",
                    "hora_apertura": "09:00:00",
                    "hora_cierre": "18:00:00",
                    "activo": True
                },
                "bloqueos": []
            }
        }