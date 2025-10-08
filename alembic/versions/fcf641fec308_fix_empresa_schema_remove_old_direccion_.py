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
    
    # Verificar si la columna existe antes de intentar eliminarla
    # (para evitar errores si ya fue eliminada)
    op.execute("""
        SET @exist := (SELECT COUNT(*) 
                       FROM information_schema.COLUMNS 
                       WHERE TABLE_SCHEMA = DATABASE() 
                       AND TABLE_NAME = 'empresa' 
                       AND COLUMN_NAME = 'direccion');
        
        SET @sqlstmt := IF(@exist > 0, 
                          'ALTER TABLE empresa DROP COLUMN direccion', 
                          'SELECT "Column direccion does not exist" AS Info');
        
        PREPARE stmt FROM @sqlstmt;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    """)


def downgrade():
    """Re-agregar columna direccion (solo por compatibilidad, no recomendado)"""
    
    # Re-agregar como nullable para evitar problemas
    op.add_column('empresa', sa.Column('direccion', sa.Text(), nullable=True))