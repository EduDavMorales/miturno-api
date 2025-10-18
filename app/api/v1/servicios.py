from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.servicio import Servicio
from app.models.empresa import Empresa
from app.models.user import Usuario
from app.schemas.servicio import ServicioCreate, ServicioUpdate, ServicioResponse
from app.api.deps import get_current_user
from app.auth.permissions import PermissionService

router = APIRouter(prefix="/servicios", tags=["Servicios"])


# ==================== ENDPOINTS ====================

@router.post("/empresa/{empresa_id}", response_model=ServicioResponse, status_code=status.HTTP_201_CREATED)
def crear_servicio(
    empresa_id: int,
    servicio_data: ServicioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Crea un nuevo servicio para una empresa.
    
    **Restricciones:**
    - Requiere permiso: servicios:crear
    - Solo puede crear servicios para su propia empresa
    """
    # Verificar permisos
    permission_service = PermissionService(db)
    if not permission_service.usuario_tiene_permiso(current_user.usuario_id, "servicios:crear", empresa_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para crear servicios"
        )
    
    # Verificar que la empresa existe y pertenece al usuario
    empresa = db.query(Empresa).filter(Empresa.empresa_id == empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )
    
    if empresa.usuario_id != current_user.usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para crear servicios en esta empresa"
        )
    
    # Crear servicio
    nuevo_servicio = Servicio(
        empresa_id=empresa_id,
        nombre=servicio_data.nombre,
        descripcion=servicio_data.descripcion,
        precio=servicio_data.precio,
        duracion_minutos=servicio_data.duracion_minutos,
        activo=servicio_data.activo
    )
    
    db.add(nuevo_servicio)
    db.commit()
    db.refresh(nuevo_servicio)
    
    return nuevo_servicio


@router.get("/empresa/{empresa_id}", response_model=List[ServicioResponse])
def listar_servicios_empresa(
    empresa_id: int,
    solo_activos: bool = True,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Lista todos los servicios de una empresa.
    
    **Parámetros:**
    - solo_activos: si True, solo retorna servicios activos
    """
    # Verificar que la empresa existe
    empresa = db.query(Empresa).filter(Empresa.empresa_id == empresa_id).first()
    if not empresa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada"
        )
    
    # Query base
    query = db.query(Servicio).filter(Servicio.empresa_id == empresa_id)
    
    # Filtrar por activos si se solicita
    if solo_activos:
        query = query.filter(Servicio.activo == True)
    
    servicios = query.all()
    return servicios


@router.get("/{servicio_id}", response_model=ServicioResponse)
def obtener_servicio(
    servicio_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Obtiene un servicio por ID.
    """
    servicio = db.query(Servicio).filter(Servicio.servicio_id == servicio_id).first()
    
    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado"
        )
    
    return servicio


@router.put("/{servicio_id}", response_model=ServicioResponse)
def actualizar_servicio(
    servicio_id: int,
    servicio_data: ServicioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Actualiza un servicio.
    
    **Restricciones:**
    - Requiere permiso: servicios:actualizar
    - Solo puede actualizar servicios de su propia empresa
    """
    # PRIMERO: Obtener servicio
    servicio = db.query(Servicio).filter(Servicio.servicio_id == servicio_id).first()
    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado"
        )
    
    # SEGUNDO: Verificar permisos (ahora sí existe servicio.empresa_id)
    permission_service = PermissionService(db)
    if not permission_service.usuario_tiene_permiso(current_user.usuario_id, "servicios:actualizar", servicio.empresa_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para actualizar servicios"
        )
    
    # Verificar que la empresa pertenece al usuario
    empresa = db.query(Empresa).filter(Empresa.empresa_id == servicio.empresa_id).first()
    if empresa.usuario_id != current_user.usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para actualizar este servicio"
        )
    
    # Actualizar campos
    update_data = servicio_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(servicio, field, value)
    
    db.commit()
    db.refresh(servicio)
    
    return servicio


@router.patch("/{servicio_id}/desactivar", status_code=status.HTTP_200_OK)
def desactivar_servicio(
    servicio_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Desactiva un servicio (soft delete).
    
    **Restricciones:**
    - Requiere permiso: servicios:desactivar
    - No elimina el registro, solo marca como inactivo
    - Mantiene trazabilidad para auditoría
    """
    # PRIMERO: Obtener servicio
    servicio = db.query(Servicio).filter(Servicio.servicio_id == servicio_id).first()
    if not servicio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Servicio no encontrado"
        )
    
    # SEGUNDO: Verificar permisos (ahora sí existe servicio.empresa_id)
    permission_service = PermissionService(db)
    if not permission_service.usuario_tiene_permiso(current_user.usuario_id, "servicios:desactivar", servicio.empresa_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para desactivar servicios"
        )
    
    # Verificar que la empresa pertenece al usuario
    empresa = db.query(Empresa).filter(Empresa.empresa_id == servicio.empresa_id).first()
    if empresa.usuario_id != current_user.usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para desactivar este servicio"
        )
    
    # Soft delete
    servicio.activo = False
    db.commit()
    db.refresh(servicio)
    
    return {
        "message": "Servicio desactivado exitosamente",
        "servicio_id": servicio_id,
        "activo": servicio.activo
    }