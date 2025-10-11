"""add_activo_to_usuario

Revision ID: 47c788241512
Revises: 83e0168915a3
Create Date: 2025-10-11

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '47c788241512'
down_revision = '83e0168915a3'  # La última migración
branch_labels = None
depends_on = None


def upgrade():
    """Agregar campos de estado activo a usuario"""
    
    # Agregar columna activo con valor por defecto TRUE
    op.add_column('usuario', 
        sa.Column('activo', sa.Boolean(), nullable=False, server_default='1')
    )
    
    # Agregar motivo de desactivación
    op.add_column('usuario',
        sa.Column('motivo_desactivacion', sa.Text(), nullable=True)
    )
    
    # Agregar fecha de desactivación
    op.add_column('usuario',
        sa.Column('fecha_desactivacion', sa.DateTime(), nullable=True)
    )
    
    # Crear índice para mejorar performance de búsquedas por estado
    op.create_index('idx_usuario_activo', 'usuario', ['activo'])


def downgrade():
    """Revertir cambios"""
    
    # Eliminar índice
    op.drop_index('idx_usuario_activo', table_name='usuario')
    
    # Eliminar columnas
    op.drop_column('usuario', 'fecha_desactivacion')
    op.drop_column('usuario', 'motivo_desactivacion')
    op.drop_column('usuario', 'activo')