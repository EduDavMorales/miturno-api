from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.core.security import verify_token
from app.models.user import Usuario, TipoUsuario
from app.schemas.auth import TokenData

# Security scheme
security = HTTPBearer()

# ============================================================================
# DEPENDENCIES BÁSICAS (EXISTENTES - MANTENER)
# ============================================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Usuario:
    """
    Dependency para obtener usuario actual autenticado.
    
    Verifica el token JWT y retorna el usuario desde la BD.
    
    Raises:
        HTTPException 401: Token inválido o usuario no encontrado
    """
    # Verificar token
    token_data: TokenData = verify_token(credentials.credentials)
    
    # Buscar usuario en BD
    user = db.query(Usuario).filter(Usuario.usuario_id == token_data.usuario_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user


def get_current_client(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """
    Dependency para verificar que el usuario actual es un cliente.
    
    DEPRECADO: Usa campo tipo_usuario. Considerar usar RBAC en su lugar.
    
    Raises:
        HTTPException 403: Usuario no es cliente
    """
    if current_user.tipo_usuario != TipoUsuario.CLIENTE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Client role required."
        )
    return current_user


def get_current_empresa(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    """
    Dependency para verificar que el usuario actual es una empresa.
    
    DEPRECADO: Usa campo tipo_usuario. Considerar usar RBAC en su lugar.
    
    Raises:
        HTTPException 403: Usuario no es empresa
    """
    if current_user.tipo_usuario != TipoUsuario.EMPRESA:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Business role required."
        )
    return current_user


# ============================================================================
# NUEVAS DEPENDENCIES - RBAC Y SEGURIDAD
# ============================================================================

def get_current_active_user(
    current_user: Usuario = Depends(get_current_user)
) -> Usuario:
    """
    Dependency para obtener usuario autenticado Y activo.
    
    Verifica que el usuario no esté deshabilitado en el sistema.
    
    Raises:
        HTTPException 403: Usuario inactivo
    """
    if not current_user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo. Contacte al administrador."
        )
    return current_user


def get_db_session() -> Session:
    """
    Dependency para obtener sesión de BD.
    
    Alias más corto de get_db para uso en decorators.
    """
    return Depends(get_db)


# ============================================================================
# DEPENDENCIES BASADAS EN RBAC (NUEVAS - RECOMENDADAS)
# ============================================================================

def get_current_user_with_role(rol_nombre: str):
    """
    Factory para crear dependency que verifica un rol específico.
    
    Uso:
        @router.get("/admin/panel")
        async def admin_panel(
            current_user = Depends(get_current_user_with_role("ADMIN_SISTEMA"))
        ):
            # Solo usuarios con rol ADMIN_SISTEMA pueden acceder
            pass
    
    Args:
        rol_nombre: Nombre del rol requerido (ej: "CLIENTE", "ADMIN_EMPRESA")
    
    Returns:
        Función dependency de FastAPI
    """
    def role_checker(
        current_user: Usuario = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> Usuario:
        from app.auth.permissions import user_has_role
        
        if not user_has_role(current_user.usuario_id, rol_nombre, db):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere rol: {rol_nombre}"
            )
        
        return current_user
    
    return role_checker


def get_empresa_owner_user(empresa_id: int):
    """
    Factory para crear dependency que verifica propiedad de empresa.
    
    Uso:
        @router.put("/empresas/{empresa_id}/servicios")
        async def actualizar_servicios(
            empresa_id: int,
            current_user = Depends(get_empresa_owner_user(empresa_id))
        ):
            # Solo dueños/admins de la empresa pueden acceder
            pass
    
    Args:
        empresa_id: ID de la empresa a verificar
    
    Returns:
        Función dependency de FastAPI
    """
    def ownership_checker(
        current_user: Usuario = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> Usuario:
        from app.utils.validators import verify_empresa_ownership
        
        verify_empresa_ownership(current_user.usuario_id, empresa_id, db)
        return current_user
    
    return ownership_checker


# ============================================================================
# HELPERS PARA USO INTERNO
# ============================================================================

def check_user_empresa_access(
    usuario_id: int,
    empresa_id: int,
    db: Session,
    required_roles: Optional[list] = None
) -> bool:
    """
    Verifica si un usuario tiene acceso a una empresa con roles específicos.
    
    Args:
        usuario_id: ID del usuario
        empresa_id: ID de la empresa
        db: Sesión de BD
        required_roles: Lista de roles aceptables (None = cualquier rol)
    
    Returns:
        True si tiene acceso
    
    Raises:
        HTTPException 403: Sin acceso
    """
    from sqlalchemy import text
    
    if required_roles is None:
        required_roles = ['DUEÑO_EMPRESA', 'ADMIN_EMPRESA', 'RECEPCIONISTA', 'EMPLEADO']
    
    query = text("""
        SELECT r.nombre
        FROM usuario_rol ur
        JOIN rol r ON ur.rol_id = r.rol_id
        WHERE ur.usuario_id = :usuario_id
        AND ur.empresa_id = :empresa_id
        AND ur.activo = 1
        AND r.nombre IN :roles
        LIMIT 1
    """)
    
    result = db.execute(query, {
        "usuario_id": usuario_id,
        "empresa_id": empresa_id,
        "roles": tuple(required_roles)
    }).fetchone()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No tienes acceso a la empresa {empresa_id}"
        )
    
    return True


def get_user_empresa_id(usuario_id: int, db: Session) -> Optional[int]:
    """
    Obtiene el ID de la empresa principal del usuario (si tiene).
    
    Útil para usuarios con rol de empresa que necesitan operar
    sobre su propia empresa sin especificar el ID explícitamente.
    
    Args:
        usuario_id: ID del usuario
        db: Sesión de BD
    
    Returns:
        ID de empresa o None
    
    Ejemplo:
        empresa_id = get_user_empresa_id(current_user.usuario_id, db)
        if empresa_id:
            # Usuario tiene empresa asociada
            pass
    """
    from sqlalchemy import text
    
    query = text("""
        SELECT ur.empresa_id
        FROM usuario_rol ur
        JOIN rol r ON ur.rol_id = r.rol_id
        WHERE ur.usuario_id = :usuario_id
        AND ur.empresa_id IS NOT NULL
        AND ur.activo = 1
        AND r.nombre IN ('DUEÑO_EMPRESA', 'ADMIN_EMPRESA')
        ORDER BY r.nivel DESC
        LIMIT 1
    """)
    
    result = db.execute(query, {"usuario_id": usuario_id}).fetchone()
    
    return result.empresa_id if result else None


# ============================================================================
# DEPENDENCIES OPCIONALES (SIN REQUERIR AUTENTICACIÓN)
# ============================================================================

def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[Usuario]:
    """
    Dependency para obtener usuario autenticado si existe, None si no.
    
    Útil para endpoints que pueden funcionar con o sin autenticación,
    mostrando diferentes datos según el estado.
    
    Returns:
        Usuario autenticado o None
    
    Ejemplo:
        @router.get("/empresas")
        async def listar_empresas(
            current_user: Optional[Usuario] = Depends(get_optional_current_user)
        ):
            if current_user:
                # Mostrar empresas personalizadas para el usuario
                pass
            else:
                # Mostrar empresas públicas
                pass
    """
    if not credentials:
        return None
    
    try:
        token_data: TokenData = verify_token(credentials.credentials)
        user = db.query(Usuario).filter(
            Usuario.usuario_id == token_data.usuario_id
        ).first()
        return user
    except:
        return None