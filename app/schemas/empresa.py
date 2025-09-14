from pydantic import BaseModel
from typing import Optional, List
from datetime import time, datetime
from decimal import Decimal

class EmpresaCreate(BaseModel):
    usuario_id: int
    categoria_id: int
    razon_social: str
    cuit: Optional[str] = None
    direccion: str
    latitud: Optional[Decimal] = None
    longitud: Optional[Decimal] = None
    descripcion: Optional[str] = None
    horario_apertura: time
    horario_cierre: time
    duracion_turno_minutos: int = 60
    logo_url: Optional[str] = None

class EmpresaResponse(BaseModel):
    empresa_id: int
    usuario_id: int
    categoria_id: int
    razon_social: str
    cuit: Optional[str] = None
    direccion: str
    latitud: Optional[Decimal] = None
    longitud: Optional[Decimal] = None
    descripcion: Optional[str] = None
    horario_apertura: time
    horario_cierre: time
    duracion_turno_minutos: int = 60
    logo_url: Optional[str] = None
    activa: bool = True
    fecha_creacion: datetime
    fecha_actualizacion: datetime
    
    class Config:
        from_attributes = True

class EmpresasListResponse(BaseModel):
    empresas: List[EmpresaResponse]
    total: int