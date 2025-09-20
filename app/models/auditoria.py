from sqlalchemy import Column, BigInteger, Integer, String, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.database import Base

class AuditoriaSistema(Base):
    __tablename__ = "auditoria_sistema"
    
    auditoria_id = Column(BigInteger, primary_key=True, index=True)
    tabla_afectada = Column(String(50), nullable=False, index=True)
    registro_id = Column(Integer, nullable=False)
    accion = Column(String(50), nullable=False, index=True)
    
    usuario_id = Column(Integer, nullable=False, index=True)
    empresa_id = Column(Integer, nullable=True, index=True)
    
    datos_anteriores = Column(JSON, nullable=True)
    datos_nuevos = Column(JSON, nullable=True)
    campos_modificados = Column(Text, nullable=True)
    
    motivo = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    fecha_cambio = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    metadatos = Column(JSON, nullable=True)
