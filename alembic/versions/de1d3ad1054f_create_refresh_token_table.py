"""create_refresh_token_table

Revision ID: de1d3ad1054f
Revises: d31c0acc9af1
Create Date: 2025-10-21 01:07:16.960635

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de1d3ad1054f'
down_revision: Union[str, None] = 'd31c0acc9af1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crear tabla refresh_token
    op.create_table(
        'refresh_token',
        sa.Column('token_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(500), nullable=False, unique=True),
        sa.Column('expira_en', sa.DateTime(), nullable=False),
        sa.Column('revocado', sa.Boolean(), default=False, nullable=False),
        sa.Column('fecha_creacion', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.PrimaryKeyConstraint('token_id'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.usuario_id'], ondelete='CASCADE')
    )
    
    # Crear índices
    op.create_index('idx_refresh_token_usuario', 'refresh_token', ['usuario_id'])
    op.create_index('idx_refresh_token_token', 'refresh_token', ['token'], unique=True)
    op.create_index('idx_refresh_token_expira', 'refresh_token', ['expira_en'])


def downgrade() -> None:
    # Eliminar índices
    op.drop_index('idx_refresh_token_expira', table_name='refresh_token')
    op.drop_index('idx_refresh_token_token', table_name='refresh_token')
    op.drop_index('idx_refresh_token_usuario', table_name='refresh_token')
    
    # Eliminar tabla
    op.drop_table('refresh_token')