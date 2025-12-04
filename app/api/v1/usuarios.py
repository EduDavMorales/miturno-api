from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.api.deps import get_current_active_user, get_db
from app.models.user import Usuario
from app.schemas.user import UsuarioUpdate, PasswordChange, UsuarioResponse
from app.core.security import get_password_hash, verify_password

router = APIRouter()


@router.get("/me", response_model=UsuarioResponse)
def get_my_profile(
    current_user: Usuario = Depends(get_current_active_user)
):
    """Obtiene el perfil del usuario autenticado"""
    return current_user


@router.patch("/me", response_model=UsuarioResponse)
def update_my_profile(
    profile_update: UsuarioUpdate,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Actualiza el perfil del usuario autenticado"""
    
    # Obtener solo campos proporcionados
    update_data = profile_update.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se proporcionaron campos para actualizar"
        )
    
    # Si cambia email, verificar que no exista
    if "email" in update_data and update_data["email"] != current_user.email:
        existing_user = db.query(Usuario).filter(
            Usuario.email == update_data["email"],
            Usuario.usuario_id != current_user.usuario_id
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El email ya está registrado"
            )
    
    # Actualizar campos
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    current_user.fecha_actualizacion = datetime.utcnow()
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.patch("/me/password", status_code=status.HTTP_200_OK)
def change_my_password(
    password_data: PasswordChange,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cambia la contraseña del usuario autenticado"""
    
    # Verificar que tenga contraseña (no es OAuth)
    if not current_user.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuario OAuth no puede cambiar contraseña"
        )
    
    # Verificar contraseña actual
    if not verify_password(password_data.current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña actual incorrecta"
        )
    
    # Actualizar contraseña
    current_user.password = get_password_hash(password_data.new_password)
    current_user.fecha_actualizacion = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Contraseña actualizada exitosamente"}


@router.delete("/me", status_code=status.HTTP_200_OK)
def delete_my_account(
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Desactiva la cuenta del usuario (soft delete)"""
    
    from app.models.turno import Turno
    
    # Desactivar usuario
    current_user.activo = False
    current_user.fecha_desactivacion = datetime.utcnow()
    current_user.motivo_desactivacion = "Desactivación solicitada por el usuario"
    
    # Cancelar turnos futuros
    turnos_cancelados = db.query(Turno).filter(
        Turno.cliente_id == current_user.usuario_id,
        Turno.fecha >= datetime.now().date(),
        Turno.estado.in_(["pendiente", "confirmado"])
    ).update({
        "estado": "cancelado",
        "motivo_cancelacion": "Cuenta de usuario desactivada",
        "fecha_cancelacion": datetime.utcnow()
    })
    
    db.commit()
    
    return {
        "message": "Cuenta desactivada exitosamente",
        "turnos_cancelados": turnos_cancelados
    }