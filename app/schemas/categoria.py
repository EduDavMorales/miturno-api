from pydantic import BaseModel, Field
from typing import Optional

class CategoriaCreate(BaseModel):
    """Schema para crear nueva categoría"""
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre de la categoría")
    descripcion: Optional[str] = Field(None, max_length=500, description="Descripción de la categoría")

class CategoriaSchema(BaseModel):
    """Schema de respuesta de categoría"""
    categoria_id: int
    nombre: str
    descripcion: Optional[str] = None
    activa: bool

    class Config:
        from_attributes = True
   
class CategoriaUpdate(BaseModel):
    """Schema para actualizar parcialmente una categoría"""
    # Todos los campos son Optional. Si se envían, se actualizan; si no, se ignoran.
    nombre: Optional[str] = Field(None, min_length=1, max_length=100, description="Nombre de la categoría")
    descripcion: Optional[str] = Field(None, max_length=500, description="Descripción de la categoría")
    activa: Optional[bool] = None