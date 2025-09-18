# app/models/horario_empresa.py
from sqlalchemy import Column, Integer, Enum, Time, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.enums import DiaSemana

class HorarioEmpresa(Base):
    __tablename__ = "horario_empresa"
    
    horario_id = Column(Integer, primary_key=True, autoincrement=True)
    empresa_id = Column(Integer, ForeignKey("empresa.empresa_id"), nullable=False)
    dia_semana = Column(Enum(DiaSemana, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    hora_apertura = Column(Time, nullable=False)
    hora_cierre = Column(Time, nullable=False)
    activo = Column(Boolean, default=True)
    
    # Relaciones
    empresa = relationship("Empresa", back_populates="horarios")