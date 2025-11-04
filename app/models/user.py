from sqlalchemy import Column, Integer, String, Enum, DateTime, Boolean, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from app.enums import TipoUsuario


class Usuario(Base):
    __tablename__ = "usuario"
    
    usuario_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=True)
    telefono = Column(String(15), nullable=True)
    tipo_usuario = Column(Enum(TipoUsuario), nullable=False, index=True)
    
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    picture_url = Column(String(500), nullable=True)
    
    # Campos de estado activo
    activo = Column(Boolean, default=True, nullable=False, index=True)
    motivo_desactivacion = Column(Text, nullable=True)
    fecha_desactivacion = Column(DateTime, nullable=True)
    
    fecha_creacion = Column(DateTime, server_default=func.now(), nullable=False)
    fecha_actualizacion = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    empresa = relationship("Empresa", back_populates="usuario", uselist=False)
    turnos_como_cliente = relationship("Turno", back_populates="cliente", foreign_keys="Turno.cliente_id")
    # Relación con tokens de reset de contraseña
    password_reset_tokens = relationship("PasswordResetToken", back_populates="usuario", cascade="all, delete-orphan")