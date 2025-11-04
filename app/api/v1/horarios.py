# app/api/v1/horarios.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date, datetime
import logging

from app.database import get_db
from app.models.user import Usuario
from app.models.empresa import Empresa
from app.models.rol import UsuarioRol
from app.core.security import get_current_user
from app.services.horario_service import HorarioService
from app.schemas.horario import (
    HorarioCreate, HorarioUpdate, HorarioResponse, HorariosListResponse,
    HorarioBulkCreate,
    BloqueoCreate, BloqueoUpdate, BloqueoResponse, BloqueosListResponse,
    DisponibilidadDia
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================
# HELPERS DE VALIDACIÓN
# ============================================

def validar_acceso_empresa(db: Session, current_user: Usuario, empresa_id: int):
    """
    Valida que el usuario tenga acceso a modificar la empresa
    Permite: Dueño de la empresa o ADMIN_EMPRESA
    """
    # Verificar que la empresa existe
    empresa = db.query(Empresa).filter(Empresa.empresa_id == empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Empresa con ID {empresa_id} no encontrada"
        )
    
    # Verificar que el usuario es dueño de la empresa
    if empresa.usuario_id == current_user.usuario_id:
        return empresa
    
    # Verificar si tiene rol ADMIN_EMPRESA en esta empresa
    usuario_rol = db.query(UsuarioRol).filter(
        UsuarioRol.usuario_id == current_user.usuario_id,
        UsuarioRol.empresa_id == empresa_id,
        UsuarioRol.rol_id == 3,  # ADMIN_EMPRESA
        UsuarioRol.activo == True
    ).first()
    
    if usuario_rol:
        return empresa
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tienes permisos para modificar esta empresa"
    )


# ============================================
# ENDPOINTS DE HORARIOS
# ============================================

@router.post(
    "/empresas/{empresa_id}/horarios",
    response_model=HorarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear horario para un día",
    description="""
    Crea un nuevo horario de atención para un día específico de la semana.
    
    **Permisos:** Solo dueño de empresa o ADMIN_EMPRESA
    
    **Validaciones:**
    - La empresa debe existir
    - No debe existir otro horario para el mismo día
    - hora_apertura debe ser menor que hora_cierre
    """
)
def crear_horario(
    empresa_id: int,
    horario: HorarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea un horario para un día de la semana"""
    try:
        # Validar acceso
        validar_acceso_empresa(db, current_user, empresa_id)
        
        # Validar que el empresa_id del path coincida con el del body
        if horario.empresa_id != empresa_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El empresa_id del path no coincide con el del body"
            )
        
        # Crear horario
        nuevo_horario = HorarioService.crear_horario(db, horario)
        
        logger.info(f"Horario creado por usuario {current_user.usuario_id} para empresa {empresa_id}")
        return nuevo_horario
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear horario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear horario"
        )


@router.post(
    "/empresas/{empresa_id}/horarios/bulk",
    response_model=HorariosListResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear múltiples horarios",
    description="""
    Crea múltiples horarios de una vez. Útil para configuración inicial.
    
    **Permisos:** Solo dueño de empresa o ADMIN_EMPRESA
    """
)
def crear_horarios_bulk(
    empresa_id: int,
    horarios_data: HorarioBulkCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea múltiples horarios de una vez"""
    try:
        # Validar acceso
        validar_acceso_empresa(db, current_user, empresa_id)
        
        # Validar empresa_id
        if horarios_data.empresa_id != empresa_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El empresa_id del path no coincide con el del body"
            )
        
        # Crear horarios
        horarios_creados = HorarioService.crear_horarios_bulk(
            db, empresa_id, horarios_data.horarios
        )
        
        logger.info(f"{len(horarios_creados)} horarios creados para empresa {empresa_id}")
        
        return HorariosListResponse(
            horarios=[HorarioResponse.model_validate(h) for h in horarios_creados],
            total=len(horarios_creados)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear horarios bulk: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear horarios"
        )


@router.get(
    "/empresas/{empresa_id}/horarios",
    response_model=HorariosListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar horarios de una empresa",
    description="""
    Obtiene todos los horarios de atención de una empresa.
    
    **Público:** No requiere autenticación
    """
)
def listar_horarios(
    empresa_id: int,
    solo_activos: bool = Query(True, description="Mostrar solo horarios activos"),
    db: Session = Depends(get_db)
):
    """Lista los horarios de una empresa"""
    try:
        # Verificar que la empresa existe
        empresa = db.query(Empresa).filter(Empresa.empresa_id == empresa_id).first()
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Empresa con ID {empresa_id} no encontrada"
            )
        
        # Obtener horarios
        horarios = HorarioService.obtener_horarios(db, empresa_id, solo_activos)
        
        return HorariosListResponse(
            horarios=[HorarioResponse.model_validate(h) for h in horarios],
            total=len(horarios)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al listar horarios: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al listar horarios"
        )


@router.get(
    "/empresas/{empresa_id}/horarios/{dia_semana}",
    response_model=HorarioResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtener horario de un día específico",
    description="""
    Obtiene el horario de un día de la semana específico.
    
    **Público:** No requiere autenticación
    """
)
def obtener_horario(
    empresa_id: int,
    dia_semana: str,
    db: Session = Depends(get_db)
):
    """Obtiene el horario de un día específico"""
    try:
        horario = HorarioService.obtener_horario_por_dia(db, empresa_id, dia_semana)
        
        if not horario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No existe horario para {dia_semana} en esta empresa"
            )
        
        return horario
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener horario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener horario"
        )


@router.put(
    "/empresas/{empresa_id}/horarios/{dia_semana}",
    response_model=HorarioResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar horario de un día",
    description="""
    Actualiza el horario de un día específico.
    
    **Permisos:** Solo dueño de empresa o ADMIN_EMPRESA
    
    **Actualización parcial:** Solo se actualizan los campos enviados
    """
)
def actualizar_horario(
    empresa_id: int,
    dia_semana: str,
    horario_data: HorarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza un horario existente"""
    try:
        # Validar acceso
        validar_acceso_empresa(db, current_user, empresa_id)
        
        # Actualizar horario
        horario_actualizado = HorarioService.actualizar_horario(
            db, empresa_id, dia_semana, horario_data
        )
        
        logger.info(f"Horario actualizado: {dia_semana} para empresa {empresa_id}")
        return horario_actualizado
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar horario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar horario"
        )

@router.patch(
    "/empresas/{empresa_id}/horarios/{dia_semana}/desactivar",
    response_model=HorarioResponse,
    status_code=status.HTTP_200_OK,
    summary="Desactivar horario (soft delete)",
    description="""
    Desactiva un horario sin eliminarlo.
    
    **Permisos:** Solo dueño de empresa o ADMIN_EMPRESA
    """
)
def desactivar_horario(
    empresa_id: int,
    dia_semana: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Desactiva un horario (soft delete)"""
    try:
        # Validar acceso
        validar_acceso_empresa(db, current_user, empresa_id)
        
        # Desactivar
        horario = HorarioService.desactivar_horario(db, empresa_id, dia_semana)
        
        logger.info(f"Horario desactivado: {dia_semana} para empresa {empresa_id}")
        return horario
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al desactivar horario: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al desactivar horario"
        )


# ============================================
# ENDPOINTS DE BLOQUEOS
# ============================================

@router.post(
    "/empresas/{empresa_id}/bloqueos",
    response_model=BloqueoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear bloqueo de horario",
    description="""
    Crea un bloqueo de horario (feriados, vacaciones, etc).
    
    **Permisos:** Solo dueño de empresa o ADMIN_EMPRESA
    
    **Tipos de bloqueo:**
    - Día completo: No especificar hora_inicio ni hora_fin
    - Parcial: Especificar ambas horas
    """
)
def crear_bloqueo(
    empresa_id: int,
    bloqueo: BloqueoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea un bloqueo de horario"""
    try:
        # Validar acceso
        validar_acceso_empresa(db, current_user, empresa_id)
        
        # Validar empresa_id
        if bloqueo.empresa_id != empresa_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El empresa_id del path no coincide con el del body"
            )
        
        # Crear bloqueo
        nuevo_bloqueo = HorarioService.crear_bloqueo(db, bloqueo)
        
        logger.info(f"Bloqueo creado por usuario {current_user.usuario_id} para empresa {empresa_id}")
        return nuevo_bloqueo
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al crear bloqueo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear bloqueo"
        )


@router.get(
    "/empresas/{empresa_id}/bloqueos",
    response_model=BloqueosListResponse,
    status_code=status.HTTP_200_OK,
    summary="Listar bloqueos de una empresa",
    description="""
    Obtiene los bloqueos de horario de una empresa.
    
    **Público:** No requiere autenticación
    
    **Filtros opcionales:** fecha_desde, fecha_hasta
    """
)
def listar_bloqueos(
    empresa_id: int,
    fecha_desde: Optional[date] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta"),
    db: Session = Depends(get_db)
):
    """Lista los bloqueos de una empresa"""
    try:
        # Verificar que la empresa existe
        empresa = db.query(Empresa).filter(Empresa.empresa_id == empresa_id).first()
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Empresa con ID {empresa_id} no encontrada"
            )
        
        # Obtener bloqueos
        bloqueos = HorarioService.obtener_bloqueos(db, empresa_id, fecha_desde, fecha_hasta)
        
        return BloqueosListResponse(
            bloqueos=[BloqueoResponse.model_validate(b) for b in bloqueos],
            total=len(bloqueos)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al listar bloqueos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al listar bloqueos"
        )


@router.put(
    "/empresas/{empresa_id}/bloqueos/{bloqueo_id}",
    response_model=BloqueoResponse,
    status_code=status.HTTP_200_OK,
    summary="Actualizar bloqueo",
    description="""
    Actualiza un bloqueo existente.
    
    **Permisos:** Solo dueño de empresa o ADMIN_EMPRESA
    """
)
def actualizar_bloqueo(
    empresa_id: int,
    bloqueo_id: int,
    bloqueo_data: BloqueoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza un bloqueo existente"""
    try:
        # Validar acceso
        validar_acceso_empresa(db, current_user, empresa_id)
        
        # Verificar que el bloqueo pertenece a la empresa
        bloqueo = HorarioService.obtener_bloqueo_por_id(db, bloqueo_id)
        if not bloqueo or bloqueo.empresa_id != empresa_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bloqueo no encontrado en esta empresa"
            )
        
        # Actualizar
        bloqueo_actualizado = HorarioService.actualizar_bloqueo(db, bloqueo_id, bloqueo_data)
        
        logger.info(f"Bloqueo {bloqueo_id} actualizado para empresa {empresa_id}")
        return bloqueo_actualizado
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar bloqueo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar bloqueo"
        )


@router.patch(
    "/empresas/{empresa_id}/bloqueos/{bloqueo_id}/desactivar",
    response_model=BloqueoResponse,
    status_code=status.HTTP_200_OK,
    summary="Desactivar bloqueo",
    description="""
    Desactiva un bloqueo de horario (soft delete).
    
    **Permisos:** Solo dueño de empresa o ADMIN_EMPRESA
    """
)
def desactivar_bloqueo(
    empresa_id: int,
    bloqueo_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Desactiva un bloqueo (soft delete)"""
    try:
        # Validar acceso
        validar_acceso_empresa(db, current_user, empresa_id)
        
        # Verificar que el bloqueo pertenece a la empresa
        bloqueo = HorarioService.obtener_bloqueo_por_id(db, bloqueo_id)
        if not bloqueo or bloqueo.empresa_id != empresa_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bloqueo no encontrado en esta empresa"
            )
        
        # Desactivar (soft delete)
        bloqueo_desactivado = HorarioService.desactivar_bloqueo(db, bloqueo_id)
        
        logger.info(f"Bloqueo {bloqueo_id} desactivado de empresa {empresa_id}")
        return bloqueo_desactivado
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al desactivar bloqueo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al desactivar bloqueo"
        )


# ============================================
# ENDPOINTS DE DISPONIBILIDAD
# ============================================

@router.get(
    "/empresas/{empresa_id}/disponibilidad",
    response_model=List[DisponibilidadDia],
    status_code=status.HTTP_200_OK,
    summary="Consultar disponibilidad",
    description="""
    Consulta la disponibilidad de una empresa en un rango de fechas.
    
    **Público:** No requiere autenticación
    
    **Retorna:** Lista de días con información de horarios y bloqueos
    """
)
def consultar_disponibilidad(
    empresa_id: int,
    fecha_desde: date = Query(..., description="Fecha desde"),
    fecha_hasta: date = Query(..., description="Fecha hasta"),
    db: Session = Depends(get_db)
):
    """Consulta la disponibilidad de una empresa"""
    try:
        # Verificar que la empresa existe
        empresa = db.query(Empresa).filter(Empresa.empresa_id == empresa_id).first()
        if not empresa:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Empresa con ID {empresa_id} no encontrada"
            )
        
        # Validar rango de fechas
        if fecha_hasta < fecha_desde:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="fecha_hasta debe ser posterior o igual a fecha_desde"
            )
        
        # Limitar rango a 90 días
        dias_diferencia = (fecha_hasta - fecha_desde).days
        if dias_diferencia > 90:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El rango de fechas no puede ser mayor a 90 días"
            )
        
        # Obtener disponibilidad
        dias_disponibles = HorarioService.obtener_dias_disponibles(
            db, empresa_id, fecha_desde, fecha_hasta
        )
        
        # Formatear respuesta
        resultado = []
        dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
        
        for dia in dias_disponibles:
            dia_semana = dias_semana[dia['fecha'].weekday()]
            
            resultado.append(DisponibilidadDia(
                fecha=dia['fecha'],
                dia_semana=dia_semana,
                abierto=dia['disponible'],
                horario=HorarioResponse.model_validate(dia['horario']) if dia['horario'] else None,
                bloqueos=[BloqueoResponse.model_validate(b) for b in dia['bloqueos']]
            ))
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al consultar disponibilidad: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al consultar disponibilidad"
        )