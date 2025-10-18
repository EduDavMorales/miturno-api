from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime

from app.database import get_db
from app.models.user import Usuario
from app.models.empresa import Empresa
from app.models.turno import Turno
from app.models.calificacion import Calificacion
from app.schemas.calificacion import (
    CalificacionCreate,
    CalificacionResponse,
    CalificacionListResponse,
    RespuestaEmpresaCreate,
    CalificacionCreateResponse,
    EstadisticasCalificaciones
)
from app.enums import EstadoTurno, TipoUsuario
from app.api.deps import get_current_user

router = APIRouter(prefix="/calificaciones", tags=["Calificaciones"])


# ==================== HELPER FUNCTIONS ====================

def actualizar_rating_empresa(db: Session, empresa_id: int):
    """Recalcula y actualiza el rating promedio de una empresa"""
    stats = db.query(
        func.avg(Calificacion.puntuacion).label('promedio'),
        func.count(Calificacion.calificacion_id).label('total')
    ).filter(
        Calificacion.empresa_id == empresa_id
    ).first()
    
    empresa = db.query(Empresa).filter(Empresa.empresa_id == empresa_id).first()
    if empresa:
        empresa.rating_promedio = round(float(stats.promedio), 2) if stats.promedio else None
        empresa.total_calificaciones = stats.total or 0
        db.commit()
        return empresa.rating_promedio
    return None


def verificar_permiso_calificar(db: Session, turno_id: int, cliente_id: int) -> Turno:
    """Verifica que el cliente pueda calificar el turno"""
    turno = db.query(Turno).filter(Turno.turno_id == turno_id).first()
    
    if not turno:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Turno no encontrado"
        )
    
    # Verificar que el turno pertenece al cliente
    if turno.cliente_id != cliente_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para calificar este turno"
        )
    
    # Verificar que el turno está completado
    if turno.estado != EstadoTurno.COMPLETADO.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo puedes calificar turnos completados"
        )
    
    # Verificar que no exista ya una calificación
    calificacion_existente = db.query(Calificacion).filter(
        Calificacion.turno_id == turno_id
    ).first()
    
    if calificacion_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este turno ya ha sido calificado"
        )
    
    return turno


# ==================== ENDPOINTS ====================

@router.post("/", response_model=CalificacionCreateResponse, status_code=status.HTTP_201_CREATED)
def crear_calificacion(
    calificacion_data: CalificacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea una nueva calificación para un turno completado.
    
    **Restricciones:**
    - Solo clientes pueden calificar
    - El turno debe estar en estado COMPLETADO
    - Solo se puede calificar una vez por turno
    - El turno debe pertenecer al cliente
    """
    # Verificar que sea un cliente
    if current_user.tipo_usuario != TipoUsuario.CLIENTE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los clientes pueden crear calificaciones"
        )
    
    # Verificar permisos y obtener turno
    turno = verificar_permiso_calificar(db, calificacion_data.turno_id, current_user.usuario_id)
    
    # Crear calificación
    nueva_calificacion = Calificacion(
        turno_id=calificacion_data.turno_id,
        cliente_id=current_user.usuario_id,
        empresa_id=turno.empresa_id,
        puntuacion=calificacion_data.puntuacion,
        comentario=calificacion_data.comentario,
        fecha_calificacion=datetime.now()
    )
    
    db.add(nueva_calificacion)
    db.commit()
    db.refresh(nueva_calificacion)
    
    # Actualizar rating de la empresa
    rating_actualizado = actualizar_rating_empresa(db, turno.empresa_id)
    
    # Construir respuesta con datos del cliente
    response_data = CalificacionResponse(
        calificacion_id=nueva_calificacion.calificacion_id,
        turno_id=nueva_calificacion.turno_id,
        cliente_id=nueva_calificacion.cliente_id,
        empresa_id=nueva_calificacion.empresa_id,
        puntuacion=nueva_calificacion.puntuacion,
        comentario=nueva_calificacion.comentario,
        respuesta_empresa=nueva_calificacion.respuesta_empresa,
        fecha_calificacion=nueva_calificacion.fecha_calificacion,
        fecha_respuesta=nueva_calificacion.fecha_respuesta,
        cliente_nombre=f"{current_user.nombre} {current_user.apellido}"
    )
    
    return CalificacionCreateResponse(
        message="Calificación creada exitosamente",
        calificacion=response_data,
        rating_actualizado=rating_actualizado
    )


@router.get("/empresa/{empresa_id}", response_model=List[CalificacionListResponse])
def listar_calificaciones_empresa(
    empresa_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista todas las calificaciones de una empresa.
    
    **Parámetros:**
    - skip: número de registros a saltar (paginación)
    - limit: cantidad máxima de registros a retornar
    """
    # Verificar que la empresa existe
    empresa = db.query(Empresa).filter(Empresa.empresa_id == empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )
    
    # Obtener calificaciones con datos del cliente
    calificaciones = db.query(
        Calificacion,
        Usuario.nombre,
        Usuario.apellido
    ).join(
        Usuario, Calificacion.cliente_id == Usuario.usuario_id
    ).filter(
        Calificacion.empresa_id == empresa_id
    ).order_by(
        Calificacion.fecha_calificacion.desc()
    ).offset(skip).limit(limit).all()
    
    # Construir respuesta
    result = []
    for calificacion, nombre, apellido in calificaciones:
        result.append(CalificacionListResponse(
            calificacion_id=calificacion.calificacion_id,
            puntuacion=calificacion.puntuacion,
            comentario=calificacion.comentario,
            respuesta_empresa=calificacion.respuesta_empresa,
            fecha_calificacion=calificacion.fecha_calificacion,
            fecha_respuesta=calificacion.fecha_respuesta,
            cliente_nombre=f"{nombre} {apellido}"
        ))
    
    return result


@router.post("/{calificacion_id}/responder", response_model=CalificacionResponse)
def responder_calificacion(
    calificacion_id: int,
    respuesta_data: RespuestaEmpresaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Permite a una empresa responder una calificación.
    
    **Restricciones:**
    - Solo empresas pueden responder
    - Solo pueden responder calificaciones de su propia empresa
    - Se puede actualizar la respuesta si ya existe
    """
    # Verificar que sea una empresa
    if current_user.tipo_usuario != TipoUsuario.DUENO.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo las empresas pueden responder calificaciones"
        )
    
    # Obtener empresa del usuario
    empresa = db.query(Empresa).filter(Empresa.usuario_id == current_user.usuario_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró empresa asociada a este usuario"
        )
    
    # Obtener calificación
    calificacion = db.query(Calificacion).filter(
        Calificacion.calificacion_id == calificacion_id
    ).first()
    
    if not calificacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Calificación no encontrada"
        )
    
    # Verificar que la calificación pertenece a la empresa
    if calificacion.empresa_id != empresa.empresa_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes responder calificaciones de otras empresas"
        )
    
    # Actualizar respuesta
    calificacion.respuesta_empresa = respuesta_data.respuesta_empresa
    calificacion.fecha_respuesta = datetime.now()
    
    db.commit()
    db.refresh(calificacion)
    
    # Obtener nombre del cliente
    cliente = db.query(Usuario).filter(Usuario.usuario_id == calificacion.cliente_id).first()
    
    return CalificacionResponse(
        calificacion_id=calificacion.calificacion_id,
        turno_id=calificacion.turno_id,
        cliente_id=calificacion.cliente_id,
        empresa_id=calificacion.empresa_id,
        puntuacion=calificacion.puntuacion,
        comentario=calificacion.comentario,
        respuesta_empresa=calificacion.respuesta_empresa,
        fecha_calificacion=calificacion.fecha_calificacion,
        fecha_respuesta=calificacion.fecha_respuesta,
        cliente_nombre=f"{cliente.nombre} {cliente.apellido}" if cliente else "Cliente"
    )


@router.get("/mis-calificaciones", response_model=List[CalificacionListResponse])
def listar_mis_calificaciones(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista las calificaciones del cliente autenticado.
    
    **Solo para clientes.**
    """
    if current_user.tipo_usuario != TipoUsuario.CLIENTE.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los clientes pueden ver sus calificaciones"
        )
    
    # Obtener calificaciones del cliente con datos de la empresa
    calificaciones = db.query(
        Calificacion,
        Empresa.razon_social
    ).join(
        Empresa, Calificacion.empresa_id == Empresa.empresa_id
    ).filter(
        Calificacion.cliente_id == current_user.usuario_id
    ).order_by(
        Calificacion.fecha_calificacion.desc()
    ).offset(skip).limit(limit).all()
    
    # Construir respuesta (usando razon_social como "cliente_nombre" para reutilizar el schema)
    result = []
    for calificacion, razon_social in calificaciones:
        result.append(CalificacionListResponse(
            calificacion_id=calificacion.calificacion_id,
            puntuacion=calificacion.puntuacion,
            comentario=calificacion.comentario,
            respuesta_empresa=calificacion.respuesta_empresa,
            fecha_calificacion=calificacion.fecha_calificacion,
            fecha_respuesta=calificacion.fecha_respuesta,
            cliente_nombre=razon_social  # Acá mostramos la empresa en lugar del cliente
        ))
    
    return result


@router.get("/empresa/{empresa_id}/estadisticas", response_model=EstadisticasCalificaciones)
def obtener_estadisticas_empresa(
    empresa_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene estadísticas de calificaciones de una empresa.
    
    **Incluye:**
    - Rating promedio
    - Total de calificaciones
    - Distribución por estrellas (1-5)
    """
    # Verificar que la empresa existe
    empresa = db.query(Empresa).filter(Empresa.empresa_id == empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )
    
    # Obtener distribución de calificaciones
    distribucion = db.query(
        Calificacion.puntuacion,
        func.count(Calificacion.calificacion_id).label('cantidad')
    ).filter(
        Calificacion.empresa_id == empresa_id
    ).group_by(
        Calificacion.puntuacion
    ).all()
    
    # Convertir a diccionario
    distribucion_dict = {str(punt): cant for punt, cant in distribucion}
    
    # Asegurar que todas las puntuaciones estén presentes
    for i in range(1, 6):
        if str(i) not in distribucion_dict:
            distribucion_dict[str(i)] = 0
    
    return EstadisticasCalificaciones(
        rating_promedio=float(empresa.rating_promedio) if empresa.rating_promedio else None,
        total_calificaciones=empresa.total_calificaciones,
        distribucion=distribucion_dict
    )