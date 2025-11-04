"""
Modelo SQLAlchemy para Invitaciones
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app.database import Base
import enum


class EstadoInvitacionEnum(str, enum.Enum):
    """Estados de invitación"""
    PENDIENTE = "pendiente"
    ACEPTADA = "aceptada"
    RECHAZADA = "rechazada"
    EXPIRADA = "expirada"


class Invitacion(Base):
    """Modelo de invitaciones para unirse a equipos de empresas"""
    
    __tablename__ = "invitacion"
    
    invitacion_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    empresa_id = Column(Integer, ForeignKey("empresa.empresa_id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    rol_nombre = Column(String(50), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    estado = Column(
        Enum(EstadoInvitacionEnum),
        nullable=False,
        default=EstadoInvitacionEnum.PENDIENTE,
        index=True
    )
    fecha_creacion = Column(DateTime, default=datetime.utcnow, nullable=False)
    fecha_expiracion = Column(DateTime, nullable=False, index=True)
    fecha_aceptacion = Column(DateTime, nullable=True)
    invitado_por = Column(Integer, ForeignKey("usuario.usuario_id"), nullable=False)
    mensaje_personalizado = Column(Text, nullable=True)
    intentos_envio = Column(Integer, default=0)
    ultimo_envio = Column(DateTime, nullable=True)
    
    # Relationships
    empresa = relationship("Empresa", back_populates="invitaciones")
    usuario_invitante = relationship("Usuario", foreign_keys=[invitado_por])
    
    def __repr__(self):
        return f"<Invitacion(id={self.invitacion_id}, email={self.email}, estado={self.estado})>"
    
    @property
    def esta_expirada(self) -> bool:
        """Verifica si la invitación está expirada"""
        return datetime.utcnow() > self.fecha_expiracion
    
    @property
    def dias_restantes(self) -> int:
        """Calcula días restantes antes de expirar"""
        if self.esta_expirada:
            return 0
        delta = self.fecha_expiracion - datetime.utcnow()
        return delta.days
    
    @property
    def puede_reenviar(self) -> bool:
        """Verifica si se puede reenviar la invitación"""
        if self.estado != EstadoInvitacionEnum.PENDIENTE:
            return False
        if self.esta_expirada:
            return False
        # Permitir reenvío cada 24 horas
        if self.ultimo_envio:
            delta = datetime.utcnow() - self.ultimo_envio
            return delta.days >= 1
        return True
    
    def marcar_como_expirada(self):
        """Marca la invitación como expirada"""
        self.estado = EstadoInvitacionEnum.EXPIRADA
    
    def marcar_como_aceptada(self):
        """Marca la invitación como aceptada"""
        self.estado = EstadoInvitacionEnum.ACEPTADA
        self.fecha_aceptacion = datetime.utcnow()
    
    def incrementar_envio(self):
        """Incrementa contador de envíos"""
        self.intentos_envio += 1
        self.ultimo_envio = datetime.utcnow()
    
    @classmethod
    def generar_fecha_expiracion(cls, dias: int = 7) -> datetime:
        """Genera fecha de expiración (por defecto 7 días)"""
        return datetime.utcnow() + timedelta(days=dias)
    
    @staticmethod
    def generar_token() -> str:
        """Genera token único para invitación"""
        import secrets
        return f"inv_{secrets.token_urlsafe(32)}"