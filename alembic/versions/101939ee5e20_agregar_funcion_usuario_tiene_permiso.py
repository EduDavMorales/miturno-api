"""agregar funcion usuario_tiene_permiso

Revision ID: 101939ee5e20
Revises: fcf641fec308
Create Date: 2025-10-10 14:43:28.482789

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '101939ee5e20'
down_revision: Union[str, None] = 'fcf641fec308'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crear función SQL para validar permisos
    op.execute("""
        DROP FUNCTION IF EXISTS usuario_tiene_permiso;
    """)
    
    op.execute("""
        CREATE FUNCTION usuario_tiene_permiso(
            p_usuario_id INT,
            p_permiso_codigo VARCHAR(100),
            p_empresa_id INT
        ) 
        RETURNS TINYINT(1)
        READS SQL DATA
        DETERMINISTIC
        BEGIN
            DECLARE tiene_permiso TINYINT(1) DEFAULT 0;
            
            SELECT COUNT(*) > 0 INTO tiene_permiso
            FROM usuario_rol ur
            INNER JOIN rol r ON ur.rol_id = r.rol_id
            INNER JOIN rol_permiso rp ON r.rol_id = rp.rol_id
            INNER JOIN permiso p ON rp.permiso_id = p.permiso_id
            WHERE ur.usuario_id = p_usuario_id
              AND p.codigo = p_permiso_codigo
              AND ur.activo = 1
              AND r.activo = 1
              AND p.activo = 1
              AND (p_empresa_id IS NULL OR ur.empresa_id = p_empresa_id OR ur.empresa_id IS NULL);
            
            RETURN tiene_permiso;
        END
    """)


def downgrade() -> None:
    # Eliminar función si hacemos rollback
    op.execute("DROP FUNCTION IF EXISTS usuario_tiene_permiso")