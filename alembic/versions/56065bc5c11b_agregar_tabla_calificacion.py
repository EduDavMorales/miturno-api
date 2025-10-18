"""agregar_tabla_calificacion

Revision ID: 56065bc5c11b
Revises: ba813fa17a5b
Create Date: 2025-10-17 23:44:03.990978

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '56065bc5c11b'
down_revision = 'ba813fa17a5b'
branch_labels = None
depends_on = None


def upgrade():
    # Crear tabla calificacion
    op.create_table(
        'calificacion',
        sa.Column('calificacion_id', sa.Integer(), nullable=False),
        sa.Column('turno_id', sa.Integer(), nullable=False),
        sa.Column('cliente_id', sa.Integer(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('puntuacion', sa.Integer(), nullable=False),
        sa.Column('comentario', sa.Text(), nullable=True),
        sa.Column('respuesta_empresa', sa.Text(), nullable=True),
        sa.Column('fecha_calificacion', sa.DateTime(), nullable=False),
        sa.Column('fecha_respuesta', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'), nullable=False),
        
        sa.PrimaryKeyConstraint('calificacion_id'),
        sa.ForeignKeyConstraint(['turno_id'], ['turno.turno_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cliente_id'], ['usuario.usuario_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.empresa_id'], ondelete='CASCADE'),
        sa.UniqueConstraint('turno_id', name='uq_calificacion_turno'),
        sa.CheckConstraint('puntuacion >= 1 AND puntuacion <= 5', name='ck_puntuacion_rango')
    )
    
    # Índices
    op.create_index('idx_calificacion_empresa', 'calificacion', ['empresa_id'])
    op.create_index('idx_calificacion_cliente', 'calificacion', ['cliente_id'])
    op.create_index('idx_calificacion_turno', 'calificacion', ['turno_id'])
    op.create_index('idx_calificacion_fecha', 'calificacion', ['fecha_calificacion'])
    
    # Agregar columnas a tabla empresa
    op.add_column('empresa', sa.Column('rating_promedio', sa.Numeric(precision=3, scale=2), nullable=True))
    op.add_column('empresa', sa.Column('total_calificaciones', sa.Integer(), server_default='0', nullable=False))


def downgrade():
    op.drop_column('empresa', 'total_calificaciones')
    op.drop_column('empresa', 'rating_promedio')
    op.drop_index('idx_calificacion_fecha', table_name='calificacion')
    op.drop_index('idx_calificacion_turno', table_name='calificacion')
    op.drop_index('idx_calificacion_cliente', table_name='calificacion')
    op.drop_index('idx_calificacion_empresa', table_name='calificacion')
    op.drop_table('calificacion')
    