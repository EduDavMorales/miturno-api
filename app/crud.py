from sqlalchemy.orm import Session
from app.models.categoria import Categoria
from app.models.turno import Turno
from app.schemas.turno import TurnoCreate
from typing import List, Optional
from datetime import datetime

def get_categorias(db: Session, skip: int = 0, limit: int = 10):
    return db.query(Categoria).filter(Categoria.activa == True).offset(skip).limit(limit).all()

def crear_turno(db: Session, turno: TurnoCreate) -> Turno:
    db_turno = Turno(
        empresa_id=turno.empresa_id,
        cliente_id=turno.cliente_id,
        servicio_id=turno.servicio_id,
        fecha=turno.fecha,
        hora=turno.hora,
        notas_cliente=turno.notas_cliente,
        notas_empresa=turno.notas_empresa,
        estado="pendiente"
    )
    db.add(db_turno)
    db.commit()
    db.refresh(db_turno)
    return db_turno

def obtener_turnos(db: Session, skip: int = 0, limit: int = 10, cliente_id: Optional[int] = None) -> List[Turno]:
    query = db.query(Turno)
    if cliente_id:
        query = query.filter(Turno.cliente_id == cliente_id)
    return query.offset(skip).limit(limit).all()

def obtener_turno_por_id(db: Session, turno_id: int) -> Optional[Turno]:
    return db.query(Turno).filter(Turno.turno_id == turno_id).first()

def cancelar_turno(db: Session, turno_id: int, cancelado_por: Optional[str] = None, motivo_cancelacion: Optional[str] = None) -> Optional[Turno]:
    turno = db.query(Turno).filter(Turno.turno_id == turno_id).first()
    if turno:
        turno.estado = "cancelado"  # o EstadoTurno.CANCELADO.value si está definido
        turno.fecha_cancelacion = datetime.utcnow()
        if cancelado_por:
            turno.cancelado_por = cancelado_por
        if motivo_cancelacion:
            turno.motivo_cancelacion = motivo_cancelacion

        db.commit()
        db.refresh(turno)
        return turno
    return None
