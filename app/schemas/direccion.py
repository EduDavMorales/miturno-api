from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DireccionCreate(BaseModel):
    calle: str
    numero: Optional[str] = None
    ciudad: str
    provincia: str
    codigo_postal: Optional[str] = None
    pais: str = 'Argentina'

class DireccionResponse(BaseModel):
    direccion_id: int
    calle: str
    numero: Optional[str] = None
    ciudad: str
    provincia: str
    codigo_postal: Optional[str] = None
    pais: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class DireccionUpdate(BaseModel):
    calle: Optional[str] = None
    numero: Optional[str] = None
    ciudad: Optional[str] = None
    provincia: Optional[str] = None
    codigo_postal: Optional[str] = None