from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_token"
    
    token_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey('usuario.usuario_id', ondelete='CASCADE'), nullable=False)
    token = Column(String(500), unique=True, nullable=False, index=True)
    expira_en = Column(DateTime, nullable=False, index=True)
    revocado = Column(Boolean, default=False, nullable=False)
    fecha_creacion = Column(DateTime, server_default=func.now(), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Relación con Usuario
    usuario = relationship("Usuario", backref="refresh_tokens")