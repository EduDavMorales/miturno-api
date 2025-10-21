"""make_telefono_nullable_for_oauth

Revision ID: d31c0acc9af1
Revises: 4c8b0335c483
Create Date: 2025-10-21 00:50:42.252661

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd31c0acc9af1'
down_revision: Union[str, None] = '4c8b0335c483'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Hacer telefono nullable para permitir OAuth
    op.alter_column('usuario', 'telefono',
                    existing_type=sa.String(15),
                    nullable=True)


def downgrade() -> None:
    # Revertir a NOT NULL
    op.alter_column('usuario', 'telefono',
                    existing_type=sa.String(15),
                    nullable=False)