"""fix_empresa_schema_remove_old_direccion_column

Revision ID: fcf641fec308
Revises: f938158bafc0
Create Date: 2025-10-08 06:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fcf641fec308'
down_revision = 'f938158bafc0'
branch_labels = None
depends_on = None


def upgrade():
    """Eliminar columna direccion antigua de tabla empresa"""
    
    # Intentar eliminar la columna, ignorar error si no existe
    try:
        op.drop_column('empresa', 'direccion')
    except Exception as e:
        # Si la columna no existe, continuar sin error
        print(f"Columna 'direccion' no existe o ya fue eliminada: {e}")
        pass


def downgrade():
    """Re-agregar columna direccion (solo por compatibilidad, no recomendado)"""
    
    # Re-agregar como nullable para evitar problemas
    op.add_column('empresa', sa.Column('direccion', sa.Text(), nullable=True))