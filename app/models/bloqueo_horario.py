# app/models/bloqueo_horario.py
from sqlalchemy import Column, Integer, Date, Time, String, Enum, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from app.enums import TipoBloqueo

class BloqueoHorario(Base):
    __tablename__ = "bloqueo_horario"
    
    bloqueo_id = Column(Integer, primary_key=True, autoincrement=True)
    empresa_id = Column(Integer, ForeignKey("empresa.empresa_id"), nullable=False)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
    hora_inicio = Column(Time)  # NULL para bloqueo de día completo
    hora_fin = Column(Time)     # NULL para bloqueo de día completo
    motivo = Column(String(255))
    tipo = Column(Enum(TipoBloqueo), default=TipoBloqueo.OTRO)
    fecha_creacion = Column(DateTime, server_default=func.now())
    
    # Relaciones
    empresa = relationship("Empresa", back_populates="bloqueos")