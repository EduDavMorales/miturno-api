from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# ===== CONVERSACIÓN =====
class ConversacionBase(BaseModel):
    cliente_id: int
    empresa_id: int

class ConversacionCreate(ConversacionBase):
    pass

class ConversacionResponse(ConversacionBase):
    conversacion_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    mensajes_no_leidos: int = 0
    
    class Config:
        from_attributes = True

# ===== MENSAJE =====
class MensajeBase(BaseModel):
    contenido: str = Field(..., min_length=1, max_length=1000, description="Contenido del mensaje")

class MensajeCreate(MensajeBase):
    conversacion_id: int

class MensajeEnviar(BaseModel):
    contenido: str = Field(..., min_length=1, max_length=1000, description="Contenido del mensaje")
    
class MensajeResponse(MensajeBase):
    mensaje_id: int
    conversacion_id: int
    remitente_tipo: str
    remitente_id: int
    leido: bool
    created_at: datetime
    deleted_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ConversacionDetalle(ConversacionResponse):
    mensajes: List[MensajeResponse] = []
    cliente_nombre: Optional[str] = None
    empresa_nombre: Optional[str] = None

class ConversacionesList(BaseModel):
    total: int
    conversaciones: List[ConversacionResponse]