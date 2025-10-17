from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Mensaje(Base):
    __tablename__ = "mensaje"
    
    mensaje_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    turno_id = Column(Integer, ForeignKey("turno.turno_id"), nullable=False)
    emisor_id = Column(Integer, ForeignKey("usuario.usuario_id"), nullable=False)
    contenido = Column(Text, nullable=False)
    fecha_envio = Column(DateTime, server_default=func.now(), nullable=False)
    leido = Column(Boolean, default=False, nullable=False)
    
    # Relaciones
    turno = relationship("Turno", back_populates="mensajes")
    emisor = relationship("Usuario", back_populates="mensajes_enviados")