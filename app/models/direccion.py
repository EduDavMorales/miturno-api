from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Direccion(Base):
    __tablename__ = "direccion"
    
    direccion_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    calle = Column(String(100), nullable=False)
    numero = Column(String(10))
    ciudad = Column(String(50), nullable=False)
    provincia = Column(String(50), nullable=False)
    codigo_postal = Column(String(10))
    pais = Column(String(50), default='Argentina')
    created_at = Column(DateTime, server_default=func.now())
    
    # Relación con empresas (una dirección puede tener múltiples empresas)
    empresas = relationship("Empresa", back_populates="direccion")