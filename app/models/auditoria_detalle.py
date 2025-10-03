from sqlalchemy import Column, BigInteger, Integer, String, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class AuditoriaDetalle(Base):
    __tablename__ = "auditoria_detalle"
    
    detalle_id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    auditoria_id = Column(BigInteger, ForeignKey("auditoria_sistema.auditoria_id"), nullable=False)
    tipo_dato = Column(Enum('anterior', 'nuevo', 'metadata'), nullable=False)
    campo_nombre = Column(String(100), nullable=False)
    campo_valor = Column(Text)
    campo_tipo = Column(String(50))
    
    # Relación con auditoría (si tienes el modelo AuditoriaSistema)
    # auditoria = relationship("AuditoriaSistema", back_populates="detalles")