"""add_apellido_to_usuario

Revision ID: b728c3d2b4af
Revises: 56065bc5c11b
Create Date: 2025-10-19 01:00:48.421995

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b728c3d2b4af'
down_revision: Union[str, None] = '56065bc5c11b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar columna apellido después de nombre
    op.add_column('usuario', 
        sa.Column('apellido', sa.String(100), nullable=True)
    )


def downgrade() -> None:
    # Revertir: eliminar columna apellido
    op.drop_column('usuario', 'apellido')