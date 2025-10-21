"""add_picture_url_to_usuario

Revision ID: f07b9a354591
Revises: 10aac0436f0c
Create Date: 2025-10-21 00:17:27.734910

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f07b9a354591'
down_revision: Union[str, None] = '10aac0436f0c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Agregar columna picture_url
    op.add_column('usuario', 
        sa.Column('picture_url', sa.String(500), nullable=True)
    )


def downgrade() -> None:
    # Eliminar columna
    op.drop_column('usuario', 'picture_url')