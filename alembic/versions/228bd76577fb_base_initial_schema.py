"""base_initial_schema

Revision ID: 228bd76577fb
Revises: 
Create Date: 2025-10-08 21:40:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '228bd76577fb'
down_revision = None  # Primera migración
branch_labels = None
depends_on = None


def upgrade():
    """Crear schema inicial completo"""
    
    # Tabla: rol
    op.create_table('rol',
        sa.Column('rol_id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=50), nullable=False),
        sa.Column('slug', sa.String(length=50), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('tipo', sa.Enum('global', 'empresa'), nullable=False),
        sa.Column('nivel', sa.Integer(), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('rol_id'),
        sa.UniqueConstraint('nombre'),
        sa.UniqueConstraint('slug')
    )
    
    # Tabla: permiso
    op.create_table('permiso',
        sa.Column('permiso_id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('recurso', sa.String(length=50), nullable=True),
        sa.Column('accion', sa.String(length=50), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('permiso_id'),
        sa.UniqueConstraint('slug')
    )
    
    # Tabla: rol_permiso
    op.create_table('rol_permiso',
        sa.Column('rol_permiso_id', sa.Integer(), nullable=False),
        sa.Column('rol_id', sa.Integer(), nullable=False),
        sa.Column('permiso_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['permiso_id'], ['permiso.permiso_id'], ),
        sa.ForeignKeyConstraint(['rol_id'], ['rol.rol_id'], ),
        sa.PrimaryKeyConstraint('rol_permiso_id')
    )
    
    # Tabla: usuario
    op.create_table('usuario',
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('apellido', sa.String(length=100), nullable=False),
        sa.Column('telefono', sa.String(length=20), nullable=True),
        sa.Column('tipo_usuario', sa.Enum('CLIENTE', 'EMPRESA', 'ADMIN'), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=True),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=True),
        sa.Column('fecha_actualizacion', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('usuario_id'),
        sa.UniqueConstraint('email')
    )
    
    # Tabla: usuario_rol
    op.create_table('usuario_rol',
        sa.Column('usuario_rol_id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('rol_id', sa.Integer(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=True),
        sa.Column('fecha_asignacion', sa.DateTime(), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['rol_id'], ['rol.rol_id'], ),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.usuario_id'], ),
        sa.PrimaryKeyConstraint('usuario_rol_id')
    )
    
    # Tabla: autorizacion_soporte
    op.create_table('autorizacion_soporte',
        sa.Column('autorizacion_id', sa.Integer(), nullable=False),
        sa.Column('usuario_solicitante_id', sa.Integer(), nullable=False),
        sa.Column('usuario_soporte_id', sa.Integer(), nullable=True),
        sa.Column('empresa_id', sa.Integer(), nullable=True),
        sa.Column('motivo', sa.Text(), nullable=False),
        sa.Column('estado', sa.Enum('PENDIENTE', 'APROBADA', 'RECHAZADA', 'REVOCADA'), nullable=False),
        sa.Column('fecha_solicitud', sa.DateTime(), nullable=True),
        sa.Column('fecha_respuesta', sa.DateTime(), nullable=True),
        sa.Column('fecha_expiracion', sa.DateTime(), nullable=True),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['usuario_solicitante_id'], ['usuario.usuario_id'], ),
        sa.ForeignKeyConstraint(['usuario_soporte_id'], ['usuario.usuario_id'], ),
        sa.PrimaryKeyConstraint('autorizacion_id')
    )
    
    # Tabla: categoria
    op.create_table('categoria',
        sa.Column('categoria_id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('activa', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('categoria_id'),
        sa.UniqueConstraint('nombre')
    )
    
    # Tabla: direccion
    op.create_table('direccion',
        sa.Column('direccion_id', sa.Integer(), nullable=False),
        sa.Column('calle', sa.String(length=255), nullable=False),
        sa.Column('numero', sa.String(length=20), nullable=True),
        sa.Column('piso', sa.String(length=10), nullable=True),
        sa.Column('departamento', sa.String(length=10), nullable=True),
        sa.Column('ciudad', sa.String(length=100), nullable=False),
        sa.Column('provincia', sa.String(length=100), nullable=False),
        sa.Column('codigo_postal', sa.String(length=20), nullable=True),
        sa.Column('pais', sa.String(length=100), nullable=True),
        sa.Column('referencia', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('direccion_id')
    )
    
    # Tabla: empresa
    op.create_table('empresa',
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('categoria_id', sa.Integer(), nullable=False),
        sa.Column('razon_social', sa.String(length=255), nullable=False),
        sa.Column('cuit', sa.String(length=20), nullable=False),
        sa.Column('latitud', sa.Numeric(precision=10, scale=8), nullable=True),
        sa.Column('longitud', sa.Numeric(precision=11, scale=8), nullable=True),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('duracion_turno_minutos', sa.Integer(), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('activa', sa.Boolean(), nullable=True),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=True),
        sa.Column('fecha_actualizacion', sa.DateTime(), nullable=True),
        sa.Column('direccion_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['categoria_id'], ['categoria.categoria_id'], ),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.usuario_id'], ),
        sa.ForeignKeyConstraint(['direccion_id'], ['direccion.direccion_id'], ),
        sa.PrimaryKeyConstraint('empresa_id'),
        sa.UniqueConstraint('cuit')
    )
    
    # Crear índice espacial para geolocalización
    op.create_index('idx_empresa_coordenadas', 'empresa', ['latitud', 'longitud'])
    
    # Tablas restantes...
    op.create_table('servicio',
        sa.Column('servicio_id', sa.Integer(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('duracion_minutos', sa.Integer(), nullable=False),
        sa.Column('precio', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.empresa_id'], ),
        sa.PrimaryKeyConstraint('servicio_id')
    )
    
    op.create_table('horario_empresa',
        sa.Column('horario_id', sa.Integer(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('dia_semana', sa.Integer(), nullable=False),
        sa.Column('hora_inicio', sa.Time(), nullable=False),
        sa.Column('hora_fin', sa.Time(), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.empresa_id'], ),
        sa.PrimaryKeyConstraint('horario_id')
    )
    
    op.create_table('turno',
        sa.Column('turno_id', sa.Integer(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('cliente_id', sa.Integer(), nullable=False),
        sa.Column('servicio_id', sa.Integer(), nullable=True),
        sa.Column('fecha_hora', sa.DateTime(), nullable=False),
        sa.Column('duracion_minutos', sa.Integer(), nullable=False),
        sa.Column('estado', sa.Enum('PENDIENTE', 'CONFIRMADO', 'CANCELADO', 'COMPLETADO'), nullable=False),
        sa.Column('notas', sa.Text(), nullable=True),
        sa.Column('fecha_creacion', sa.DateTime(), nullable=True),
        sa.Column('fecha_actualizacion', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['cliente_id'], ['usuario.usuario_id'], ),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.empresa_id'], ),
        sa.ForeignKeyConstraint(['servicio_id'], ['servicio.servicio_id'], ),
        sa.PrimaryKeyConstraint('turno_id')
    )
    
    op.create_table('bloqueo_horario',
        sa.Column('bloqueo_id', sa.Integer(), nullable=False),
        sa.Column('empresa_id', sa.Integer(), nullable=False),
        sa.Column('fecha_inicio', sa.DateTime(), nullable=False),
        sa.Column('fecha_fin', sa.DateTime(), nullable=False),
        sa.Column('motivo', sa.String(length=255), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresa.empresa_id'], ),
        sa.PrimaryKeyConstraint('bloqueo_id')
    )
    
    op.create_table('mensaje',
        sa.Column('mensaje_id', sa.Integer(), nullable=False),
        sa.Column('turno_id', sa.Integer(), nullable=False),
        sa.Column('remitente_id', sa.Integer(), nullable=False),
        sa.Column('contenido', sa.Text(), nullable=False),
        sa.Column('fecha_envio', sa.DateTime(), nullable=True),
        sa.Column('leido', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['remitente_id'], ['usuario.usuario_id'], ),
        sa.ForeignKeyConstraint(['turno_id'], ['turno.turno_id'], ),
        sa.PrimaryKeyConstraint('mensaje_id')
    )
    
    # Tablas de auditoría
    op.create_table('auditoria_sistema',
        sa.Column('auditoria_id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=True),
        sa.Column('accion', sa.String(length=100), nullable=False),
        sa.Column('tabla_afectada', sa.String(length=100), nullable=True),
        sa.Column('registro_id', sa.Integer(), nullable=True),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('fecha_hora', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.usuario_id'], ),
        sa.PrimaryKeyConstraint('auditoria_id')
    )
    
    op.create_table('auditoria_detalle',
        sa.Column('detalle_id', sa.Integer(), nullable=False),
        sa.Column('auditoria_id', sa.Integer(), nullable=False),
        sa.Column('campo', sa.String(length=100), nullable=False),
        sa.Column('valor_anterior', sa.Text(), nullable=True),
        sa.Column('valor_nuevo', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['auditoria_id'], ['auditoria_sistema.auditoria_id'], ),
        sa.PrimaryKeyConstraint('detalle_id')
    )


def downgrade():
    """Eliminar todas las tablas"""
    op.drop_table('auditoria_detalle')
    op.drop_table('auditoria_sistema')
    op.drop_table('mensaje')
    op.drop_table('bloqueo_horario')
    op.drop_table('turno')
    op.drop_table('horario_empresa')
    op.drop_table('servicio')
    op.drop_index('idx_empresa_coordenadas', table_name='empresa')
    op.drop_table('empresa')
    op.drop_table('direccion')
    op.drop_table('categoria')
    op.drop_table('autorizacion_soporte')
    op.drop_table('usuario_rol')
    op.drop_table('usuario')
    op.drop_table('rol_permiso')
    op.drop_table('permiso')
    op.drop_table('rol')