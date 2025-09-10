from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class Categoria(Base):
    __tablename__ = "categoria"
    
    categoria_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nombre = Column(String(100), unique=True, nullable=False, index=True)
    descripcion = Column(String(500))
    activa = Column(Boolean, default=True, nullable=False)
    
    # Relaciones
    empresas = relationship("Empresa", back_populates="categoria")