from sqlalchemy import Column, Integer, String, ForeignKey, DECIMAL, Text, Time, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Empresa(Base):
    __tablename__ = "empresa"
    
    empresa_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuario.usuario_id"), unique=True, nullable=False)
    categoria_id = Column(Integer, ForeignKey("categoria.categoria_id"), nullable=False)
    razon_social = Column(String(200), nullable=False)
    cuit = Column(String(13), unique=True)
    direccion = Column(String(300), nullable=False)
    latitud = Column(DECIMAL(10, 8))
    longitud = Column(DECIMAL(11, 8))
    descripcion = Column(Text)
    horario_apertura = Column(Time, nullable=False)
    horario_cierre = Column(Time, nullable=False)
    duracion_turno_minutos = Column(Integer, default=60)
    logo_url = Column(String(500))
    activa = Column(Boolean, default=True, nullable=False)
    fecha_creacion = Column(DateTime, server_default=func.now())
    fecha_actualizacion = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relaciones
    usuario = relationship("Usuario", back_populates="empresa")
    categoria = relationship("Categoria", back_populates="empresas")
    turnos = relationship("Turno", back_populates="empresa")
    servicios = relationship("Servicio", back_populates="empresa")