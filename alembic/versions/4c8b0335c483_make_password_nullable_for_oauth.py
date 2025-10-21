"""make_password_nullable_for_oauth

Revision ID: 4c8b0335c483
Revises: f07b9a354591
Create Date: 2025-10-21 00:38:03.800991

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c8b0335c483'
down_revision: Union[str, None] = 'f07b9a354591'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Hacer password nullable para permitir OAuth
    op.alter_column('usuario', 'password',
                    existing_type=sa.String(255),
                    nullable=True)


def downgrade() -> None:
    # Revertir a NOT NULL (solo si no hay usuarios OAuth)
    op.alter_column('usuario', 'password',
                    existing_type=sa.String(255),
                    nullable=False)