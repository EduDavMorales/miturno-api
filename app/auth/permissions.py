# app/auth/permissions.py
"""
Sistema de validación de permisos RBAC para MiTurno API
Proporciona decoradores y funciones helper para control de acceso basado en roles
"""

from typing import Optional, List, Dict, Any, Callable
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import Depends, HTTPException, status
from app.database import get_db
from app.api.deps import get_current_user


# ============================================================================
# CLASE DE SERVICIO EXISTENTE (MANTENER)
# ============================================================================

class PermissionService:
    """Servicio básico para gestionar permisos"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def usuario_tiene_permiso(
        self, 
        usuario_id: int, 
        permiso_codigo: str, 
        empresa_id: Optional[int] = None
    ) -> bool:
        """Verificar si un usuario tiene un permiso específico"""
        try:
            query = text("""
                SELECT usuario_tiene_permiso(:usuario_id, :permiso_codigo, :empresa_id) as tiene_permiso
            """)
            
            result = self.db.execute(query, {
                "usuario_id": usuario_id,
                "permiso_codigo": permiso_codigo,
                "empresa_id": empresa_id
            }).fetchone()
            
            return bool(result.tiene_permiso)
            
        except Exception as e:
            print(f"Error verificando permiso: {e}")
            return False
    
    def obtener_permisos_usuario(self, usuario_id: int) -> List[Dict[str, Any]]:
        """Obtener permisos básicos de un usuario"""
        try:
            # Query corregido: usar tablas reales y extraer acción del código
            query = text("""
                SELECT DISTINCT
                    p.codigo as permiso_codigo,
                    p.nombre as permiso_nombre,
                    p.categoria as recurso,
                    SUBSTRING_INDEX(SUBSTRING_INDEX(p.codigo, ':', 2), ':', -1) as accion
                FROM usuario_rol ur
                JOIN rol r ON ur.rol_id = r.rol_id
                JOIN rol_permiso rp ON r.rol_id = rp.rol_id
                JOIN permiso p ON rp.permiso_id = p.permiso_id
                WHERE ur.usuario_id = :usuario_id 
                AND ur.activo = 1
                AND r.activo = 1
                AND p.activo = 1
                ORDER BY p.categoria, p.codigo
            """)
            
            result = self.db.execute(query, {"usuario_id": usuario_id}).fetchall()
            return [dict(row._mapping) for row in result]
            
        except Exception as e:
            print(f"Error obteniendo permisos: {e}")
            return []


# ============================================================================
# FUNCIONES HELPER (NUEVAS)
# ============================================================================

def user_has_permission(
    usuario_id: int,
    permission_code: str,
    db: Session,
    empresa_id: Optional[int] = None
) -> bool:
    """
    Verifica si un usuario tiene un permiso específico.
    
    Args:
        usuario_id: ID del usuario
        permission_code: Código del permiso (ej: "turno:crear:propio")
        db: Sesión de base de datos
        empresa_id: ID de empresa para permisos contextuales
    
    Returns:
        True si tiene el permiso, False en caso contrario
    
    Ejemplo:
        if user_has_permission(user.usuario_id, "empresa:actualizar:propia", db):
            # Usuario puede actualizar
            pass
    """
    service = PermissionService(db)
    return service.usuario_tiene_permiso(usuario_id, permission_code, empresa_id)


def get_user_permissions(usuario_id: int, db: Session) -> List[Dict[str, Any]]:
    """
    Obtiene todos los permisos activos de un usuario.
    
    Args:
        usuario_id: ID del usuario
        db: Sesión de base de datos
    
    Returns:
        Lista de diccionarios con información de permisos
    """
    service = PermissionService(db)
    return service.obtener_permisos_usuario(usuario_id)


# ============================================================================
# DECORADORES DE FASTAPI (NUEVOS)
# ============================================================================

def require_permission(permission_code: str, empresa_id_param: Optional[str] = None):
    """
    Decorator de FastAPI para requerir un permiso específico.
    
    Uso básico:
        @router.get("/empresas/{empresa_id}/turnos")
        async def listar_turnos(
            empresa_id: int,
            current_user = Depends(require_permission("turno:leer:empresa"))
        ):
            # Solo usuarios con permiso pueden acceder
            pass
    
    Uso con contexto de empresa:
        @router.put("/empresas/{empresa_id}/servicios/{servicio_id}")
        async def actualizar_servicio(
            empresa_id: int,
            servicio_id: int,
            current_user = Depends(require_permission(
                "servicio:actualizar",
                empresa_id_param="empresa_id"
            ))
        ):
            # Valida permiso en contexto de esa empresa específica
            pass
    
    Args:
        permission_code: Código del permiso requerido
        empresa_id_param: Nombre del parámetro de path que contiene empresa_id
    
    Returns:
        Función de dependencia de FastAPI
    
    Raises:
        HTTPException 401: No autenticado
        HTTPException 403: Sin permiso
    """
    def permission_checker(
        current_user = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        # Verificar autenticación
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No autenticado"
            )
        
        # Verificar permiso
        empresa_id = None
        # TODO: Extraer empresa_id del path si empresa_id_param está definido
        # Esto requiere access a los path params, se implementará en siguiente iteración
        
        if not user_has_permission(current_user.usuario_id, permission_code, db, empresa_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso denegado. Se requiere: {permission_code}"
            )
        
        return current_user
    
    return permission_checker


def require_any_permission(permission_codes: List[str]):
    """
    Decorator para requerir AL MENOS UNO de varios permisos (OR lógico).
    
    Uso:
        @router.get("/empresas/{empresa_id}/empleados")
        async def listar_empleados(
            current_user = Depends(require_any_permission([
                "empresa:gestionar:usuarios",
                "sistema:administrar:usuarios"
            ]))
        ):
            # Usuario necesita uno de los dos permisos
            pass
    
    Args:
        permission_codes: Lista de códigos de permisos
    
    Returns:
        Función de dependencia de FastAPI
    
    Raises:
        HTTPException 403: No tiene ninguno de los permisos
    """
    def permission_checker(
        current_user = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No autenticado"
            )
        
        # Verificar si tiene al menos uno de los permisos
        has_permission = any(
            user_has_permission(current_user.usuario_id, code, db)
            for code in permission_codes
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso denegado. Se requiere uno de: {', '.join(permission_codes)}"
            )
        
        return current_user
    
    return permission_checker


def require_all_permissions(permission_codes: List[str]):
    """
    Decorator para requerir TODOS los permisos especificados (AND lógico).
    
    Uso:
        @router.delete("/empresas/{empresa_id}")
        async def eliminar_empresa(
            current_user = Depends(require_all_permissions([
                "empresa:eliminar:propia",
                "empresa:gestionar:usuarios"
            ]))
        ):
            # Usuario necesita ambos permisos
            pass
    
    Args:
        permission_codes: Lista de códigos de permisos
    
    Returns:
        Función de dependencia de FastAPI
    
    Raises:
        HTTPException 403: Falta al menos un permiso
    """
    def permission_checker(
        current_user = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No autenticado"
            )
        
        # Verificar todos los permisos
        missing_permissions = [
            code for code in permission_codes
            if not user_has_permission(current_user.usuario_id, code, db)
        ]
        
        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permisos faltantes: {', '.join(missing_permissions)}"
            )
        
        return current_user
    
    return permission_checker


# ============================================================================
# HELPERS DE ROLES (NUEVO - TRANSICIÓN DE tipo_usuario)
# ============================================================================

def user_has_role(usuario_id: int, rol_nombre: str, db: Session) -> bool:
    """
    Verifica si un usuario tiene un rol específico.
    
    Args:
        usuario_id: ID del usuario
        rol_nombre: Nombre del rol (ej: "CLIENTE", "ADMIN_EMPRESA")
        db: Sesión de BD
    
    Returns:
        True si tiene el rol activo
    """
    try:
        query = text("""
            SELECT COUNT(*) as count
            FROM usuario_rol ur
            JOIN rol r ON ur.rol_id = r.rol_id
            WHERE ur.usuario_id = :usuario_id
            AND r.nombre = :rol_nombre
            AND ur.activo = 1
            AND r.activo = 1
        """)
        
        result = db.execute(query, {
            "usuario_id": usuario_id,
            "rol_nombre": rol_nombre
        }).fetchone()
        
        return result.count > 0
        
    except Exception as e:
        print(f"Error verificando rol: {e}")
        return False


def get_user_roles(usuario_id: int, db: Session) -> List[str]:
    """
    Obtiene todos los roles activos de un usuario.
    
    Args:
        usuario_id: ID del usuario
        db: Sesión de BD
    
    Returns:
        Lista de nombres de roles
    """
    try:
        query = text("""
            SELECT r.nombre
            FROM usuario_rol ur
            JOIN rol r ON ur.rol_id = r.rol_id
            WHERE ur.usuario_id = :usuario_id
            AND ur.activo = 1
            AND r.activo = 1
            ORDER BY r.nivel DESC
        """)
        
        result = db.execute(query, {"usuario_id": usuario_id}).fetchall()
        return [row.nombre for row in result]
        
    except Exception as e:
        print(f"Error obteniendo roles: {e}")
        return []


# ============================================================================
# ASIGNACIÓN DE ROLES (NUEVO)
# ============================================================================

def assign_role(
    usuario_id: int,
    rol_nombre: str,
    db: Session,
    empresa_id: Optional[int] = None
) -> bool:
    """
    Asigna un rol a un usuario, opcionalmente en contexto de una empresa.
    
    Args:
        usuario_id: ID del usuario
        rol_nombre: Nombre del rol (ej: "CLIENTE", "ADMIN_EMPRESA")
        db: Sesión de BD
        empresa_id: ID de empresa (requerido para roles de empresa)
    
    Returns:
        True si se asignó exitosamente
    
    Raises:
        HTTPException 400: Datos inválidos o rol no existe
        HTTPException 409: Usuario ya tiene ese rol
    
    Ejemplo de uso:
        # Asignar rol de cliente (global)
        assign_role(user.usuario_id, "CLIENTE", db)
        
        # Asignar rol de admin en una empresa específica
        assign_role(user.usuario_id, "ADMIN_EMPRESA", db, empresa_id=5)
    """
    from fastapi import HTTPException, status
    
    try:
        # 1. Verificar que el rol existe
        query_rol = text("""
            SELECT rol_id, tipo 
            FROM rol 
            WHERE nombre = :rol_nombre AND activo = 1
        """)
        
        rol = db.execute(query_rol, {"rol_nombre": rol_nombre}).fetchone()
        
        if not rol:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rol '{rol_nombre}' no encontrado"
            )
        
        rol_id = rol.rol_id
        rol_tipo = rol.tipo
        
        # 2. Validar empresa_id según tipo de rol
        if rol_tipo == "EMPRESA" and empresa_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El rol '{rol_nombre}' requiere empresa_id"
            )
        
        if rol_tipo == "SISTEMA" and empresa_id is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El rol '{rol_nombre}' no debe tener empresa_id"
            )
        
        # 3. Verificar si ya existe la asignación
        query_existe = text("""
            SELECT usuario_rol_id, activo
            FROM usuario_rol
            WHERE usuario_id = :usuario_id
            AND rol_id = :rol_id
            AND (:empresa_id IS NULL OR empresa_id = :empresa_id)
        """)
        
        existe = db.execute(query_existe, {
            "usuario_id": usuario_id,
            "rol_id": rol_id,
            "empresa_id": empresa_id
        }).fetchone()
        
        if existe:
            # Si existe pero está inactivo, reactivarlo
            if not existe.activo:
                query_activar = text("""
                    UPDATE usuario_rol
                    SET activo = 1,
                        fecha_asignacion = CURRENT_TIMESTAMP
                    WHERE usuario_rol_id = :usuario_rol_id
                """)
                db.execute(query_activar, {"usuario_rol_id": existe.usuario_rol_id})
                db.commit()
                return True
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Usuario ya tiene el rol '{rol_nombre}'"
                )
        
        # 4. Crear nueva asignación de rol
        query_insert = text("""
            INSERT INTO usuario_rol (usuario_id, rol_id, empresa_id, activo)
            VALUES (:usuario_id, :rol_id, :empresa_id, 1)
        """)
        
        db.execute(query_insert, {
            "usuario_id": usuario_id,
            "rol_id": rol_id,
            "empresa_id": empresa_id
        })
        
        db.commit()
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error asignando rol: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error asignando rol al usuario"
        )


def remove_role(
    usuario_id: int,
    rol_nombre: str,
    db: Session,
    empresa_id: Optional[int] = None
) -> bool:
    """
    Remueve (desactiva) un rol de un usuario.
    
    Args:
        usuario_id: ID del usuario
        rol_nombre: Nombre del rol a remover
        db: Sesión de BD
        empresa_id: ID de empresa (si es rol de empresa)
    
    Returns:
        True si se removió exitosamente
    
    Raises:
        HTTPException 404: Usuario no tiene ese rol
    """
    from fastapi import HTTPException, status
    
    try:
        # Obtener rol_id
        query_rol = text("""
            SELECT rol_id FROM rol 
            WHERE nombre = :rol_nombre AND activo = 1
        """)
        
        rol = db.execute(query_rol, {"rol_nombre": rol_nombre}).fetchone()
        
        if not rol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rol '{rol_nombre}' no encontrado"
            )
        
        # Desactivar asignación
        query_update = text("""
            UPDATE usuario_rol
            SET activo = 0
            WHERE usuario_id = :usuario_id
            AND rol_id = :rol_id
            AND (:empresa_id IS NULL OR empresa_id = :empresa_id)
            AND activo = 1
        """)
        
        result = db.execute(query_update, {
            "usuario_id": usuario_id,
            "rol_id": rol.rol_id,
            "empresa_id": empresa_id
        })
        
        db.commit()
        
        if result.rowcount == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario no tiene el rol '{rol_nombre}' activo"
            )
        
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error removiendo rol: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error removiendo rol del usuario"
        )