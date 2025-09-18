# app/api/v1/turnos.py
from fastapi import APIRouter, Depends, HTTPException, Body, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional

from app.database import get_db
from app.core.security import get_current_user
from app.models.user import Usuario
from app.services.turno_service import TurnoService
from app.schemas.turno import (
    # Schemas originales (mantener compatibilidad)
    TurnoSchema, 
    TurnoCreate, 
    TurnoCancelacionSchema,
    # Nuevos schemas
    DisponibilidadRequest,
    DisponibilidadResponse,
    ReservaTurnoRequest,
    TurnoResponse,
    ModificarTurnoRequest,
    FiltrosTurnos,
    TurnosList
)
from app.crud import crear_turno, obtener_turnos, obtener_turno_por_id, cancelar_turno

router = APIRouter()

# =============================================
# ENDPOINTS NUEVOS CON TURNOSERVICE
# =============================================

@router.get("/empresas/{empresa_id}/disponibilidad", response_model=DisponibilidadResponse)
def consultar_disponibilidad(
    empresa_id: int,
    fecha: str = Query(..., description="Fecha en formato YYYY-MM-DD"),
    servicio_id: Optional[int] = Query(None, description="ID del servicio específico"),
    db: Session = Depends(get_db)
):
    """
    Consulta la disponibilidad de turnos para una empresa en una fecha específica
    """
    from datetime import datetime
    
    try:
        # Parsear fecha
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de fecha inválido. Use YYYY-MM-DD"
        )
    
    # Crear request object
    request = DisponibilidadRequest(fecha=fecha_obj, servicio_id=servicio_id)
    
    # Usar TurnoService
    service = TurnoService(db)
    return service.obtener_disponibilidad(empresa_id, request)

@router.post("/turnos/reservar", response_model=TurnoResponse)
def reservar_turno(
    request: ReservaTurnoRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reserva un turno para el usuario autenticado
    """
    service = TurnoService(db)
    return service.reservar_turno(current_user.usuario_id, request)

@router.get("/mis-turnos", response_model=TurnosList)
def obtener_mis_turnos(
    pagina: int = Query(1, ge=1, description="Número de página"),
    por_pagina: int = Query(10, ge=1, le=100, description="Elementos por página"),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    estado: Optional[str] = Query(None, description="Estado del turno"),
    empresa_id: Optional[int] = Query(None, description="ID de la empresa"),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene los turnos del usuario autenticado con filtros y paginación
    """
    from datetime import datetime
    from app.enums import EstadoTurno
    
    # Construir filtros
    filtros = FiltrosTurnos()
    
    if fecha_desde:
        try:
            filtros.fecha_desde = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de fecha_desde inválido. Use YYYY-MM-DD"
            )
    
    if fecha_hasta:
        try:
            filtros.fecha_hasta = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de fecha_hasta inválido. Use YYYY-MM-DD"
            )
    
    if estado:
        try:
            filtros.estado = EstadoTurno(estado)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estado inválido. Valores permitidos: {[e.value for e in EstadoTurno]}"
            )
    
    if empresa_id:
        filtros.empresa_id = empresa_id
    
    # Usar TurnoService
    service = TurnoService(db)
    return service.obtener_turnos_usuario(
        usuario_id=current_user.usuario_id,
        filtros=filtros,
        pagina=pagina,
        por_pagina=por_pagina
    )

@router.put("/turnos/{turno_id}", response_model=TurnoResponse)
def modificar_turno(
    turno_id: int,
    request: ModificarTurnoRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Modifica un turno existente del usuario autenticado
    """
    service = TurnoService(db)
    return service.modificar_turno(turno_id, current_user.usuario_id, request)

@router.put("/turnos/{turno_id}/cancelar", response_model=TurnoResponse)
def cancelar_turno_usuario(
    turno_id: int,
    motivo: str = Body(..., embed=True),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancela un turno del usuario autenticado (actualización de estado)
    """
    service = TurnoService(db)
    return service.cancelar_turno(turno_id, current_user.usuario_id, motivo)

# =============================================
# ENDPOINTS ORIGINALES (COMPATIBILIDAD)
# Mantener estos endpoints para no romper código existente
# =============================================

@router.post("/turnos", response_model=TurnoSchema)
def crear_turno_api(turno: TurnoCreate, db: Session = Depends(get_db)):
    """
    ENDPOINT LEGACY: Crear turno (mantener compatibilidad)
    Recomendado usar POST /turnos/reservar en su lugar
    """
    try:
        nuevo_turno = crear_turno(db, turno)
        return nuevo_turno
    except IntegrityError as e:
        db.rollback()
        if "turno.unique_empresa_fecha_hora" in str(e.orig):
            raise HTTPException(status_code=400, detail="El horario ya está reservado para esta empresa.")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.get("/turnos", response_model=List[TurnoSchema])
def listar_turnos(
    skip: int = 0, 
    limit: int = 10, 
    cliente_id: Optional[int] = None, 
    db: Session = Depends(get_db)
):
    """
    ENDPOINT LEGACY: Listar turnos (mantener compatibilidad)
    Recomendado usar GET /mis-turnos en su lugar
    """
    turnos = obtener_turnos(db, skip=skip, limit=limit, cliente_id=cliente_id)
    return turnos

@router.get("/turnos/{turno_id}", response_model=TurnoSchema)
def obtener_turno(turno_id: int, db: Session = Depends(get_db)):
    """
    ENDPOINT LEGACY: Obtener turno específico
    """
    turno = obtener_turno_por_id(db, turno_id)
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado")
    return turno

@router.delete("/turnos/{turno_id}", response_model=TurnoSchema, deprecated=True)
def cancelar_turno_api(
    turno_id: int,
    cancelacion: TurnoCancelacionSchema = Body(...),
    db: Session = Depends(get_db)
):
    """
    ENDPOINT LEGACY: Cancelar turno (mantener compatibilidad)
    ⚠️ DEPRECATED: Usar PUT /turnos/{turno_id}/cancelar en su lugar
    """
    turno = cancelar_turno(
        db,
        turno_id,
        cancelado_por=cancelacion.cancelado_por,
        motivo_cancelacion=cancelacion.motivo_cancelacion
    )
    if not turno:
        raise HTTPException(status_code=404, detail="Turno no encontrado o no pudo ser cancelado")
    return turno