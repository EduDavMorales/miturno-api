from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from .direccion import DireccionResponse, DireccionCreate

class EmpresaCreate(BaseModel):
    usuario_id: int
    categoria_id: int
    razon_social: str
    cuit: Optional[str] = None
    direccion: DireccionCreate  
    latitud: Optional[Decimal] = None
    longitud: Optional[Decimal] = None
    descripcion: Optional[str] = None
    duracion_turno_minutos: int = 60
    logo_url: Optional[str] = None

class EmpresaResponse(BaseModel):
    empresa_id: int
    usuario_id: int
    categoria_id: int
    razon_social: str
    cuit: Optional[str] = None
    direccion_id: Optional[int] = None  
    direccion: Optional[DireccionResponse] = None 
    latitud: Optional[Decimal] = None
    longitud: Optional[Decimal] = None
    descripcion: Optional[str] = None
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

# Schema para actualización (PATCH)
class EmpresaUpdate(BaseModel):
    razon_social: Optional[str] = None
    cuit: Optional[str] = None
    descripcion: Optional[str] = None
    duracion_turno_minutos: Optional[int] = None
    logo_url: Optional[str] = None
    # Nota: direccion se actualizará por separado usando DireccionUpdate