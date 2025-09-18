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
            query = text("""
                SELECT DISTINCT
                    permiso_codigo,
                    permiso_nombre,
                    recurso,
                    accion
                FROM usuario_permisos_activos 
                WHERE usuario_id = :usuario_id 
                ORDER BY recurso, accion
            """)
            
            result = self.db.execute(query, {"usuario_id": usuario_id}).fetchall()
            return [dict(row._mapping) for row in result]
            
        except Exception as e:
            print(f"Error obteniendo permisos: {e}")
            return []