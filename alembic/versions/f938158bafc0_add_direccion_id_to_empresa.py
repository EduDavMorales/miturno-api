"""add_direccion_id_to_empresa

Revision ID: f938158bafc0
Revises: 034c254ecc95
Create Date: 2025-10-08 05:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f938158bafc0'
down_revision = '034c254ecc95'
branch_labels = None
depends_on = None


def upgrade():
    """Agregar columna direccion_id a tabla empresa"""
    
    # Agregar columna direccion_id (nullable porque empresas existentes no tienen dirección normalizada)
    op.add_column('empresa', sa.Column('direccion_id', sa.Integer(), nullable=True))
    
    # Agregar foreign key constraint
    op.create_foreign_key(
        'fk_empresa_direccion',
        'empresa', 'direccion',
        ['direccion_id'], ['direccion_id']
    )


def downgrade():
    """Eliminar columna direccion_id de tabla empresa"""
    
    # Eliminar foreign key constraint primero
    op.drop_constraint('fk_empresa_direccion', 'empresa', type_='foreignkey')
    
    # Eliminar columna
    op.drop_column('empresa', 'direccion_id')