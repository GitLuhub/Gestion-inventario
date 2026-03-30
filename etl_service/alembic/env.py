"""
env.py — Entorno de ejecución de migraciones Alembic para ETL Service.

Lee la URL de la BD desde ETL_DB_URL (env var) o desde alembic.ini como fallback.
Soporta migraciones online (con conexión activa) y offline (genera SQL sin conectar).
"""

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Configuración de logging de Alembic
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Sobreescribir sqlalchemy.url desde env var si está definida
etl_db_url = os.getenv(
    'ETL_DB_URL',
    os.getenv('DATABASE_URL', config.get_main_option('sqlalchemy.url'))
)
config.set_main_option('sqlalchemy.url', etl_db_url)

# Metadatos de los modelos — importar aquí cuando se use autogenerate
# from src.database.models import Base
# target_metadata = Base.metadata
target_metadata = None


def run_migrations_offline() -> None:
    """Genera SQL sin conexión a la BD (útil para revisión de migraciones)."""
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
    """Ejecuta migraciones con una conexión activa a la BD."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
