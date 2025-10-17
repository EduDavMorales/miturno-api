"""replace_mensaje_with_conversacion_system

Revision ID: ba813fa17a5b
Revises: 47c788241512
Create Date: 2025-10-17 01:08:26.791111

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba813fa17a5b'
down_revision: Union[str, None] = '47c788241512'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Eliminar tabla mensaje vieja
    op.drop_table('mensaje')
    
    # Crear tabla conversacion
    op.create_table(
        'conversacion',
        sa.Column('conversacion_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('cliente_id', sa.Integer(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['cliente_id'], ['usuario.usuario_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.empresa_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('conversacion_id')
    )
    op.create_index('idx_conversacion_cliente', 'conversacion', ['cliente_id'], unique=False)
    op.create_index('idx_conversacion_empresa', 'conversacion', ['empresa_id'], unique=False)
    op.create_index('idx_conversacion_unique', 'conversacion', ['cliente_id', 'empresa_id'], unique=True)
    
    # Crear tabla mensaje nueva
    op.create_table(
        'mensaje',
        sa.Column('mensaje_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('conversacion_id', sa.Integer(), nullable=False),
        sa.Column('remitente_tipo', sa.Enum('cliente', 'empresa', name='remitenteenum'), nullable=False),
        sa.Column('remitente_id', sa.Integer(), nullable=False),
        sa.Column('contenido', sa.Text(), nullable=False),
        sa.Column('leido', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['conversacion_id'], ['conversacion.conversacion_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('mensaje_id')
    )
    op.create_index('idx_mensaje_conversacion', 'mensaje', ['conversacion_id'], unique=False)
    op.create_index('idx_mensaje_leido', 'mensaje', ['leido'], unique=False)
    op.create_index('idx_mensaje_created', 'mensaje', ['created_at'], unique=False)
    
    # Ajustes de índices detectados
    op.drop_index('idx_empresa_coordenadas', table_name='empresa')
    op.drop_index('idx_usuario_activo', table_name='usuario')
    op.create_index(op.f('ix_usuario_activo'), 'usuario', ['activo'], unique=False)


def downgrade() -> None:
    # Revertir cambios
    op.drop_index(op.f('ix_usuario_activo'), table_name='usuario')
    op.create_index('idx_usuario_activo', 'usuario', ['activo'], unique=False)
    op.create_index('idx_empresa_coordenadas', 'empresa', ['latitud', 'longitud'], unique=False)
    
    op.drop_table('mensaje')
    op.drop_table('conversacion')
    
    # Recrear mensaje vieja (opcional, para rollback completo)
    op.create_table(
        'mensaje',
        sa.Column('mensaje_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('turno_id', sa.Integer(), nullable=False),
        sa.Column('emisor_id', sa.Integer(), nullable=False),
        sa.Column('contenido', sa.Text(), nullable=False),
        sa.Column('fecha_envio', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('leido', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['turno_id'], ['turno.turno_id']),
        sa.ForeignKeyConstraint(['emisor_id'], ['usuario.usuario_id']),
        sa.PrimaryKeyConstraint('mensaje_id')
    )
