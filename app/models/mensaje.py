from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class RemitenteEnum(enum.Enum):
    cliente = "cliente"
    empresa = "empresa"

class Conversacion(Base):
    __tablename__ = "conversacion"
    
    conversacion_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cliente_id = Column(Integer, ForeignKey("usuario.usuario_id", ondelete="CASCADE"), nullable=False)
    empresa_id = Column(Integer, ForeignKey("empresa.empresa_id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    mensajes = relationship("Mensaje", back_populates="conversacion", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_conversacion_cliente', 'cliente_id'),
        Index('idx_conversacion_empresa', 'empresa_id'),
        Index('idx_conversacion_unique', 'cliente_id', 'empresa_id', unique=True),
    )

class Mensaje(Base):
    __tablename__ = "mensaje"
    
    mensaje_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    conversacion_id = Column(Integer, ForeignKey("conversacion.conversacion_id", ondelete="CASCADE"), nullable=False)
    remitente_tipo = Column(SQLEnum(RemitenteEnum), nullable=False)
    remitente_id = Column(Integer, nullable=False)
    contenido = Column(Text, nullable=False)
    leido = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete
    
    # Relationships
    conversacion = relationship("Conversacion", back_populates="mensajes")
    
    # Indexes
    __table_args__ = (
        Index('idx_mensaje_conversacion', 'conversacion_id'),
        Index('idx_mensaje_leido', 'leido'),
        Index('idx_mensaje_created', 'created_at'),
    )