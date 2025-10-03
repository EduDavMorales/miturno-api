from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

# Importar la configuración de tu app
from app.config import settings
from app.database import Base

# Importar TODOS los modelos para que Alembic los detecte
from app.models.user import Usuario
from app.models.empresa import Empresa
from app.models.categoria import Categoria
from app.models.direccion import Direccion
from app.models.turno import Turno
from app.models.servicio import Servicio
from app.models.horario_empresa import HorarioEmpresa
from app.models.bloqueo_horario import BloqueoHorario
from app.models.mensaje import Mensaje
from app.models.rol import Rol
from app.models.auditoria import AuditoriaSistema
from app.models.auditoria_detalle import AuditoriaDetalle

# this is the Alembic Config object
config = context.config

# Configurar la URL de la base de datos desde settings
config.set_main_option('sqlalchemy.url', settings.get_database_url())

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()