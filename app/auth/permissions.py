# app/auth/permissions.py
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text

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
            # Query corregido: usar tablas reales en lugar de vista
            query = text("""
                SELECT DISTINCT
                    p.codigo as permiso_codigo,
                    p.nombre as permiso_nombre,
                    p.categoria as recurso,
                    'READ' as accion
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