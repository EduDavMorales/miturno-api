"""seed_roles_y_categorias_base

Revision ID: 034c254ecc95
Revises: 9e275309deea
Create Date: 2025-10-08 04:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '034c254ecc95'
down_revision = '9e275309deea'
branch_labels = None
depends_on = None


def upgrade():
    """Insertar roles y categorías base del sistema"""
    
    # Insertar roles base
    op.execute("""
        INSERT INTO rol (rol_id, nombre, slug, descripcion, tipo, nivel, activo) 
        VALUES
        (1, 'SUPERADMIN', 'superadmin', 'Administrador del sistema con acceso total', 'global', 100, 1),
        (2, 'SOPORTE', 'soporte', 'Personal de soporte técnico', 'global', 80, 1),
        (3, 'ADMIN_EMPRESA', 'admin-empresa', 'Administrador de empresa', 'empresa', 60, 1),
        (4, 'EMPRESA', 'empresa', 'Usuario empresa estándar', 'empresa', 50, 1),
        (5, 'EMPLEADO', 'empleado', 'Empleado de empresa', 'empresa', 40, 1),
        (6, 'CLIENTE', 'cliente', 'Cliente final', 'global', 20, 1),
        (7, 'INVITADO', 'invitado', 'Usuario invitado con acceso limitado', 'global', 10, 1)
        ON DUPLICATE KEY UPDATE nombre=nombre;
    """)
    
    # Insertar categorías base
    op.execute("""
        INSERT INTO categoria (nombre, descripcion, activa) 
        VALUES
        ('Barbería', 'Servicios de corte y arreglo de cabello y barba', 1),
        ('Peluquería', 'Servicios de estilismo y tratamiento capilar', 1),
        ('Salud', 'Consultorios médicos y servicios de salud', 1),
        ('Belleza', 'Servicios de estética y cuidado personal', 1),
        ('Deportes', 'Gimnasios y centros deportivos', 1),
        ('Educación', 'Centros educativos y capacitación', 1),
        ('Gastronomía', 'Restaurantes y servicios de comida', 1),
        ('Automotor', 'Talleres mecánicos y servicios vehiculares', 1)
        ON DUPLICATE KEY UPDATE nombre=nombre;
    """)


def downgrade():
    """Eliminar datos seed"""
    
    # Eliminar categorías (en orden inverso)
    op.execute("DELETE FROM categoria WHERE nombre IN ('Barbería', 'Peluquería', 'Salud', 'Belleza', 'Deportes', 'Educación', 'Gastronomía', 'Automotor')")
    
    # Eliminar roles
    op.execute("DELETE FROM rol WHERE rol_id BETWEEN 1 AND 7")