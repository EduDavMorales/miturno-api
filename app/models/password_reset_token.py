from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class PasswordResetToken(Base):
    """
    Modelo para tokens de recuperación de contraseña.
    
    Gestiona el proceso de reset de contraseña mediante tokens únicos
    que expiran después de un tiempo determinado.
    """
    __tablename__ = "password_reset_token"
    
    # Primary Key
    token_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Key
    usuario_id = Column(Integer, ForeignKey('usuario.usuario_id', ondelete='CASCADE'), nullable=False)
    
    # Token único
    token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Fechas
    fecha_creacion = Column(DateTime, nullable=False, server_default=func.current_timestamp())
    fecha_expiracion = Column(DateTime, nullable=False, index=True)
    
    # Estado del token
    usado = Column(Boolean, nullable=False, default=False, server_default='0', index=True)
    fecha_uso = Column(DateTime, nullable=True)
    
    # Metadata de seguridad
    ip_solicitud = Column(String(45), nullable=True)  # IP desde donde se solicitó
    ip_uso = Column(String(45), nullable=True)        # IP desde donde se usó
    
    # Relationships
    usuario = relationship("Usuario", back_populates="password_reset_tokens")
    
    def __repr__(self):
        return f"<PasswordResetToken(token_id={self.token_id}, usuario_id={self.usuario_id}, usado={self.usado})>"
    
    def is_expired(self) -> bool:
        """Verifica si el token ha expirado."""
        from datetime import datetime
        return datetime.utcnow() > self.fecha_expiracion
    
    def is_valid(self) -> bool:
        """Verifica si el token es válido (no usado y no expirado)."""
        return not self.usado and not self.is_expired()