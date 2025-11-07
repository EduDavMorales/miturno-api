# app/schemas/turno.py
from pydantic import BaseModel, constr, Field, validator
from datetime import date, time, datetime
from typing import Optional, List
from enum import Enum
from app.enums import EstadoTurno

class CanceladoPorEnum(str, Enum):
    cliente = "cliente"
    empresa = "empresa"

class TurnoBase(BaseModel):
    empresa_id: int
    cliente_id: int
    servicio_id: Optional[int] = None
    fecha: date
    hora: time
    notas_cliente: Optional[str] = None
    notas_empresa: Optional[str] = None
    cancelado_por: Optional[CanceladoPorEnum] = None
    motivo_cancelacion: Optional[constr(max_length=280)] = None

class TurnoCreate(TurnoBase):
    pass

class TurnoSchema(TurnoBase):
    turno_id: int
    estado: EstadoTurno
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    fecha_cancelacion: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Esquema para la cancelación de turno
class TurnoCancelacionSchema(BaseModel):
    cancelado_por: CanceladoPorEnum
    motivo_cancelacion: Optional[constr(max_length=280)] = None

# =============================================
# SCHEMAS ADICIONALES PARA ENDPOINTS API
# =============================================

# Schemas para disponibilidad
class DisponibilidadRequest(BaseModel):
    """Request para consultar disponibilidad de una empresa"""
    fecha_desde: date = Field(..., description="Fecha desde para consultar disponibilidad")
    fecha_hasta: Optional[date] = Field(None, description="Fecha hasta (opcional, si no se especifica usa fecha_desde)")
    servicio_id: Optional[int] = Field(None, description="ID del servicio específico (opcional)")
    
    @validator('fecha_desde')
    def validar_fecha_desde_futura(cls, v):
        if v < date.today():
            raise ValueError('La fecha_desde debe ser hoy o en el futuro')
        return v
    
    @validator('fecha_hasta')
    def validar_fecha_hasta(cls, v, values):
        if v:
            # Validar que sea futura
            if v < date.today():
                raise ValueError('La fecha_hasta debe ser hoy o en el futuro')
            
            # Validar que sea mayor o igual a fecha_desde
            if 'fecha_desde' in values and v < values['fecha_desde']:
                raise ValueError('fecha_hasta debe ser mayor o igual a fecha_desde')
            
            # Limitar rango máximo a 30 días
            if 'fecha_desde' in values and (v - values['fecha_desde']).days > 30:
                raise ValueError('El rango máximo es de 30 días')
        
        return v

class SlotDisponible(BaseModel):
    """Representa un slot de tiempo disponible"""
    fecha: date = Field(..., description="Fecha del slot")
    hora_inicio: time = Field(..., description="Hora de inicio del slot")
    hora_fin: time = Field(..., description="Hora de fin del slot")
    servicio_id: int = Field(..., description="ID del servicio")
    servicio_nombre: str = Field(..., description="Nombre del servicio")
    duracion_minutos: int = Field(..., description="Duración en minutos")
    precio: float = Field(..., description="Precio del servicio")

class DisponibilidadDia(BaseModel):
    """Disponibilidad de un día específico"""
    fecha: date = Field(..., description="Fecha")
    slots_disponibles: List[SlotDisponible] = Field(default_factory=list, description="Slots disponibles en este día")
    total_slots: int = Field(..., description="Total de slots disponibles en este día")

class DisponibilidadResponse(BaseModel):
    """Respuesta con disponibilidad de turnos"""
    fecha_desde: date = Field(..., description="Fecha desde consultada")
    fecha_hasta: date = Field(..., description="Fecha hasta consultada")
    empresa_id: int = Field(..., description="ID de la empresa")
    empresa_nombre: str = Field(..., description="Nombre de la empresa")
    dias: List[DisponibilidadDia] = Field(default_factory=list, description="Disponibilidad por día")
    total_dias_con_disponibilidad: int = Field(..., description="Total de días con al menos un slot disponible")
    total_slots: int = Field(..., description="Total de slots disponibles en todo el rango")

# Schema para reservar turnos
class ReservaTurnoRequest(BaseModel):
    """Request para reservar un turno"""
    empresa_id: int = Field(..., description="ID de la empresa")
    servicio_id: int = Field(..., description="ID del servicio")
    fecha: date = Field(..., description="Fecha del turno")
    hora: time = Field(..., description="Hora del turno")
    notas_cliente: Optional[str] = Field(None, max_length=500, description="Notas adicionales del cliente")
    
    @validator('fecha')
    def validar_fecha_reserva(cls, v):
        if v < date.today():
            raise ValueError('No se puede reservar en fechas pasadas')
        return v
    
    @validator('notas_cliente')
    def validar_notas(cls, v):
        if v and len(v.strip()) == 0:
            return None
        return v

# Schema para respuesta completa de turno
class TurnoResponse(BaseModel):
    """Respuesta completa con información del turno y entidades relacionadas"""
    turno_id: int
    empresa_id: int
    empresa_nombre: str
    cliente_id: int
    cliente_nombre: str
    servicio_id: Optional[int]
    servicio_nombre: Optional[str]
    fecha: date
    hora: time
    hora_fin: time
    estado: EstadoTurno
    notas_cliente: Optional[str]
    notas_empresa: Optional[str]
    precio: float
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    fecha_cancelacion: Optional[datetime]
    cancelado_por: Optional[CanceladoPorEnum]
    motivo_cancelacion: Optional[str]
    
    class Config:
        from_attributes = True

# Schema para modificar turnos
class ModificarTurnoRequest(BaseModel):
    """Request para modificar un turno existente"""
    fecha: Optional[date] = Field(None, description="Nueva fecha del turno")
    hora: Optional[time] = Field(None, description="Nueva hora del turno")
    servicio_id: Optional[int] = Field(None, description="Nuevo servicio")
    notas_cliente: Optional[str] = Field(None, max_length=500, description="Nuevas notas del cliente")
    
    @validator('fecha')
    def validar_nueva_fecha(cls, v):
        if v and v < date.today():
            raise ValueError('La nueva fecha debe ser hoy o en el futuro')
        return v
    
    @validator('*', pre=True)
    def validar_al_menos_un_campo(cls, v, values):
        if not any(values.values()) and v is None:
            raise ValueError('Debe proporcionar al menos un campo para modificar')
        return v

# Schema para listas paginadas de turnos
class TurnosList(BaseModel):
    """Lista paginada de turnos"""
    turnos: List[TurnoResponse] = Field(default_factory=list, description="Lista de turnos")
    total: int = Field(..., description="Total de turnos")
    pagina: int = Field(..., description="Página actual")
    por_pagina: int = Field(..., description="Elementos por página")
    total_paginas: int = Field(..., description="Total de páginas")
    tiene_siguiente: bool = Field(..., description="Indica si hay página siguiente")
    tiene_anterior: bool = Field(..., description="Indica si hay página anterior")

# Filtros para búsqueda de turnos
class FiltrosTurnos(BaseModel):
    """Filtros para búsqueda de turnos"""
    fecha_desde: Optional[date] = Field(None, description="Fecha desde")
    fecha_hasta: Optional[date] = Field(None, description="Fecha hasta")
    estado: Optional[EstadoTurno] = Field(None, description="Estado del turno")
    empresa_id: Optional[int] = Field(None, description="ID de la empresa")
    servicio_id: Optional[int] = Field(None, description="ID del servicio")
    
    @validator('fecha_hasta')
    def validar_rango_fechas(cls, v, values):
        if v and 'fecha_desde' in values and values['fecha_desde']:
            if v < values['fecha_desde']:
                raise ValueError('fecha_hasta debe ser mayor o igual a fecha_desde')
        return v