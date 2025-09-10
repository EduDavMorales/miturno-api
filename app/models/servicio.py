from sqlalchemy import Column, Integer, String, ForeignKey, Text, DECIMAL, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Servicio(Base):
    __tablename__ = "servicio"
    
    servicio_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    empresa_id = Column(Integer, ForeignKey("empresa.empresa_id"), nullable=False)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    duracion_minutos = Column(Integer, default=60)
    precio = Column(DECIMAL(10, 2), default=0.00)
    activo = Column(Boolean, default=True, nullable=False)
    fecha_creacion = Column(DateTime, server_default=func.now())
    
    # Relaciones
    empresa = relationship("Empresa", back_populates="servicios")
    turnos = relationship("Turno", back_populates="servicio")