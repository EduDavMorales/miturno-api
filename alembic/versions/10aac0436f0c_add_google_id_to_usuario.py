"""add_google_id_to_usuario

Revision ID: 10aac0436f0c
Revises: b728c3d2b4af
Create Date: 2025-10-20 22:34:23.722400

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '10aac0436f0c'
down_revision: Union[str, None] = 'b728c3d2b4af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Agregar columna google_id
    op.add_column('usuario', 
        sa.Column('google_id', sa.String(255), nullable=True)
    )
    
    # Crear índice único para búsquedas rápidas
    op.create_index('idx_usuario_google_id', 'usuario', ['google_id'], unique=True)


def downgrade():
    # Eliminar índice
    op.drop_index('idx_usuario_google_id', table_name='usuario')
    
    # Eliminar columna
    op.drop_column('usuario', 'google_id')