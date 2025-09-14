from pydantic import BaseModel, constr
from datetime import date, time, datetime
from typing import Optional
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
    motivo_cancelacion: Optional[constr(max_length=280)] = None  # Limite 280 caracteres

class TurnoCreate(TurnoBase):
    pass

class TurnoSchema(TurnoBase):
    turno_id: int
    estado: EstadoTurno
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    fecha_cancelacion: Optional[datetime] = None

    class Config:
        orm_mode = True

# Esquema para la cancelación de turno
class TurnoCancelacionSchema(BaseModel):
    cancelado_por: CanceladoPorEnum
    motivo_cancelacion: Optional[constr(max_length=280)] = None