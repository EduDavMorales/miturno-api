from pydantic import BaseModel
from typing import Optional

class CategoriaSchema(BaseModel):
    categoria_id: int
    nombre: str
    descripcion: Optional[str] = None
    activa: bool

    class Config:
        orm_mode = True
