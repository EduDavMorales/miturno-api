"""add_recepcionista_deactivate_invitado

Revision ID: 83e0168915a3
Revises: 101939ee5e20
Create Date: 2025-10-10 23:18:53.126182

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '83e0168915a3'
down_revision: Union[str, None] = '101939ee5e20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1. Desactivar rol INVITADO
    op.execute("""
        UPDATE rol 
        SET activo = FALSE 
        WHERE nombre = 'INVITADO'
    """)
    
    # 2. Agregar rol RECEPCIONISTA (solo si no existe)
    op.execute("""
        INSERT INTO rol (nombre, slug, descripcion, tipo, nivel, activo)
        SELECT 'RECEPCIONISTA', 'recepcionista', 
               'Gestiona turnos y clientes de la empresa', 
               'empresa', 45, TRUE
        WHERE NOT EXISTS (
            SELECT 1 FROM rol WHERE nombre = 'RECEPCIONISTA'
        )
    """)


def downgrade():
    # 1. Reactivar INVITADO
    op.execute("""
        UPDATE rol 
        SET activo = TRUE 
        WHERE nombre = 'INVITADO'
    """)
    
    # 2. Eliminar RECEPCIONISTA
    op.execute("""
        DELETE FROM rol 
        WHERE nombre = 'RECEPCIONISTA'
    """)