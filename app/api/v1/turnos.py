from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from app.database import get_db
from app.schemas.turno import TurnoSchema, TurnoCreate, TurnoCancelacionSchema
from app.crud import crear_turno, obtener_turnos, obtener_turno_por_id, cancelar_turno

router = APIRouter()

@router.post("/turnos", response_model=TurnoSchema)
def crear_turno_api(turno: TurnoCreate, db: Session = Depends(get_db)):
    try:
        nuevo_turno = crear_turno(db, turno)
        return nuevo_turno
    except IntegrityError as e:
        db.rollback()
        if "turno.unique_empresa_fecha_hora" in str(e.orig):
            raise HTTPException(status_code=400, detail="El horario ya está reservado para esta empresa.")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/turnos", response_model=List[TurnoSchema])
def listar_turnos(skip: int = 0, limit: int = 10, cliente_id: Optional[int] = None, db: Session = Depends(get_db)):
    turnos = obtener_turnos(db, skip=skip, limit=limit, cliente_id=cliente_id)
    return turnos

@router.get("/turnos/{turno_id}", response_model=TurnoSchema)
def obtener_turno(turno_id: int, db: Session = Depends(get_db)):
    turno = obtener_turno_por_id(db, turno_id)
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return turno

@router.delete("/turnos/{turno_id}", response_model=TurnoSchema)
def cancelar_turno_api(
    turno_id: int,
    cancelacion: TurnoCancelacionSchema = Body(...),
    db: Session = Depends(get_db)
):
    turno = cancelar_turno(
        db,
        turno_id,
        cancelado_por=cancelacion.cancelado_por,
        motivo_cancelacion=cancelacion.motivo_cancelacion
    )
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado o no pudo ser cancelado")
    return turno
