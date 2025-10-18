from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, CheckConstraint, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Calificacion(Base):
    __tablename__ = "calificacion"
    
    calificacion_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    turno_id = Column(Integer, ForeignKey("turno.turno_id", ondelete="CASCADE"), nullable=False, unique=True)
    cliente_id = Column(Integer, ForeignKey("usuario.usuario_id", ondelete="CASCADE"), nullable=False, index=True)
    empresa_id = Column(Integer, ForeignKey("empresa.empresa_id", ondelete="CASCADE"), nullable=False, index=True)
    
    puntuacion = Column(Integer, nullable=False)
    comentario = Column(Text, nullable=True)
    respuesta_empresa = Column(Text, nullable=True)
    
    fecha_calificacion = Column(DateTime, nullable=False, default=func.now(), index=True)
    fecha_respuesta = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Check constraint para puntuación
    __table_args__ = (
        CheckConstraint('puntuacion >= 1 AND puntuacion <= 5', name='ck_puntuacion_rango'),
    )
    
    # Relaciones
    turno = relationship("Turno", back_populates="calificacion")
    cliente = relationship("Usuario", foreign_keys=[cliente_id])
    empresa = relationship("Empresa", back_populates="calificaciones")