from sqlalchemy import Column, Integer, String, Enum, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class TipoUsuario(str, enum.Enum):
    CLIENTE = "cliente"
    EMPRESA = "empresa"


class Usuario(Base):
    __tablename__ = "usuario"
    
    usuario_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    nombre = Column(String(100), nullable=False)
    telefono = Column(String(15), nullable=False)
    tipo_usuario = Column(Enum(TipoUsuario), nullable=False, index=True)
    fecha_creacion = Column(DateTime, server_default=func.now(), nullable=False)
    fecha_actualizacion = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    empresa = relationship("Empresa", back_populates="usuario", uselist=False)
    turnos_como_cliente = relationship("Turno", back_populates="cliente", foreign_keys="Turno.cliente_id")
    mensajes_enviados = relationship("Mensaje", back_populates="emisor")