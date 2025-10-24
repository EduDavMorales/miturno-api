"""create password_reset_token table

Revision ID: ddc02c990b10
Revises: de1d3ad1054f
Create Date: 2025-10-24 23:07:05.111699

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ddc02c990b10'
down_revision: Union[str, None] = 'de1d3ad1054f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Crear tabla password_reset_token
    op.create_table(
        'password_reset_token',
        sa.Column('token_id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(255), nullable=False),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('fecha_expiracion', sa.DateTime(), nullable=False),
        sa.Column('usado', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('fecha_uso', sa.DateTime(), nullable=True),
        sa.Column('ip_solicitud', sa.String(45), nullable=True),
        sa.Column('ip_uso', sa.String(45), nullable=True),
        
        sa.PrimaryKeyConstraint('token_id'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.usuario_id'], ondelete='CASCADE'),
        
        mysql_charset='utf8mb4',
        mysql_collate='utf8mb4_unicode_ci'
    )
    
    # Crear índices para optimizar consultas
    op.create_index('idx_token', 'password_reset_token', ['token'], unique=True)
    op.create_index('idx_usuario_id', 'password_reset_token', ['usuario_id'])
    op.create_index('idx_fecha_expiracion', 'password_reset_token', ['fecha_expiracion'])
    op.create_index('idx_usado', 'password_reset_token', ['usado'])


def downgrade():
    # Eliminar índices
    op.drop_index('idx_usado', table_name='password_reset_token')
    op.drop_index('idx_fecha_expiracion', table_name='password_reset_token')
    op.drop_index('idx_usuario_id', table_name='password_reset_token')
    op.drop_index('idx_token', table_name='password_reset_token')
    
    # Eliminar tabla
    op.drop_table('password_reset_token')