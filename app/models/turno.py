from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Time, Enum, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base
from app.enums import EstadoTurno

class CanceladoPorEnum(PyEnum):
    cliente = "cliente"
    empresa = "empresa"

class Turno(Base):
    __tablename__ = "turno"

    turno_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    empresa_id = Column(Integer, ForeignKey("empresa.empresa_id"), nullable=False)
    cliente_id = Column(Integer, ForeignKey("usuario.usuario_id"), nullable=False)
    servicio_id = Column(Integer, ForeignKey("servicio.servicio_id"))
    fecha = Column(Date, nullable=False, index=True)
    hora = Column(Time, nullable=False, index=True)
    estado = Column(
        Enum(EstadoTurno, values_callable=lambda obj: [e.value for e in obj]),
        default=EstadoTurno.PENDIENTE.value,
        nullable=False
    )
    notas_cliente = Column(Text)
    notas_empresa = Column(Text)
    fecha_creacion = Column(DateTime, server_default=func.now())
    fecha_actualizacion = Column(DateTime, server_default=func.now(), onupdate=func.now())
    fecha_cancelacion = Column(DateTime)

    # Nuevos campos para registro de cancelación
    cancelado_por = Column(Enum(CanceladoPorEnum), nullable=True)
    motivo_cancelacion = Column(Text, nullable=True)

    # Relaciones
    empresa = relationship("Empresa", back_populates="turnos")
    cliente = relationship("Usuario", back_populates="turnos_como_cliente", foreign_keys=[cliente_id])
    servicio = relationship("Servicio", back_populates="turnos")
    
