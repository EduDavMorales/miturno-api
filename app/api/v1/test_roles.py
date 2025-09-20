# app/api/v1/test_roles.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import get_current_user  
from app.auth.permissions import PermissionService
from app.models.user import Usuario

router = APIRouter(prefix="/test", tags=["Test Roles"])

@router.get("/mis-permisos")
async def test_mis_permisos(
    current_user: Usuario = Depends(get_current_user),  
    db: Session = Depends(get_db)
):
    """Endpoint de prueba para verificar permisos del usuario"""
    try:
        permission_service = PermissionService(db)
        permisos = permission_service.obtener_permisos_usuario(current_user.usuario_id)
        
        return {
            "status": "success",
            "usuario_id": current_user.usuario_id,
            "email": current_user.email,  
            "total_permisos": len(permisos),
            "permisos": permisos
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo permisos: {str(e)}"
        )

@router.get("/verificar-permiso/{permiso_codigo}")
async def test_verificar_permiso(
    permiso_codigo: str,
    empresa_id: int = None,
    current_user: Usuario = Depends(get_current_user),  
    db: Session = Depends(get_db)
):
    """Probar verificación de un permiso específico"""
    try:
        permission_service = PermissionService(db)
        tiene_permiso = permission_service.usuario_tiene_permiso(
            current_user.usuario_id,
            permiso_codigo,
            empresa_id
        )
        
        return {
            "status": "success",
            "usuario_id": current_user.usuario_id,
            "email": current_user.email,  
            "permiso_codigo": permiso_codigo,
            "empresa_id": empresa_id,
            "tiene_permiso": tiene_permiso
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error verificando permiso: {str(e)}"
        )