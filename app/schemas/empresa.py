from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from .direccion import DireccionResponse, DireccionCreate, DireccionUpdate  # ← AGREGADO DireccionUpdate

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

# ← ELIMINADO DireccionUpdate duplicado (ahora se importa desde direccion.py)
        
class EmpresaUpdate(BaseModel):
    """
    Schema para actualizar empresa.
    Todos los campos son opcionales (permite actualización parcial).
    """
    # Campos de tabla EMPRESA
    razon_social: Optional[str] = Field(None, min_length=3, max_length=200)
    cuit: Optional[str] = Field(None, pattern=r'^\d{11}$')
    descripcion: Optional[str] = Field(None, max_length=5000)
    logo_url: Optional[str] = Field(None, max_length=500)
    categoria_id: Optional[int] = Field(None, gt=0)
    duracion_turno_minutos: Optional[int] = Field(None, ge=15, le=240)
    latitud: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitud: Optional[Decimal] = Field(None, ge=-180, le=180)
    
    # Dirección (anidada)
    direccion: Optional[DireccionUpdate] = None
    
    @validator('cuit')
    def validar_cuit(cls, v):
        if v:
            if not v.isdigit():
                raise ValueError('CUIT debe contener solo números')
            if len(v) != 11:
                raise ValueError('CUIT debe tener exactamente 11 dígitos')
        return v
    
    @validator('duracion_turno_minutos')
    def validar_duracion(cls, v):
        if v and v % 5 != 0:
            raise ValueError('La duración debe ser múltiplo de 5 minutos')
        return v
    
    class Config:
        from_attributes = True