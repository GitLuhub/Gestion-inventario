"""Tablas de control para historial de ejecuciones del ETL

Revision ID: 0001
Revises:
Create Date: 2026-03-30

Crea las tablas de control internas del ETL:
  - etl_job_runs:  registra cada ejecución del pipeline (inicio, fin, estado)
  - etl_job_errors: almacena errores detallados por ejecución

Estas tablas NO afectan a Odoo — son internas del ETL para observabilidad
y diagnóstico sin depender de Loki o logs externos.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # etl_job_runs — una fila por ejecución del pipeline ETL
    # ------------------------------------------------------------------
    op.create_table(
        'etl_job_runs',
        sa.Column('id',         sa.Integer(),     primary_key=True, autoincrement=True),
        sa.Column('job_name',   sa.String(120),   nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status',     sa.String(20),    nullable=False, server_default='running',
                  comment='running | success | error | partial'),
        sa.Column('records_extracted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('records_loaded',    sa.Integer(), nullable=False, server_default='0'),
        sa.Column('records_failed',    sa.Integer(), nullable=False, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
    )
    op.create_index('ix_etl_job_runs_job_name',   'etl_job_runs', ['job_name'])
    op.create_index('ix_etl_job_runs_started_at', 'etl_job_runs', ['started_at'])
    op.create_index('ix_etl_job_runs_status',     'etl_job_runs', ['status'])

    # ------------------------------------------------------------------
    # etl_job_errors — detalles de errores vinculados a una ejecución
    # ------------------------------------------------------------------
    op.create_table(
        'etl_job_errors',
        sa.Column('id',         sa.Integer(),  primary_key=True, autoincrement=True),
        sa.Column('run_id',     sa.Integer(),  sa.ForeignKey('etl_job_runs.id', ondelete='CASCADE'),
                  nullable=False, index=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('NOW()')),
        sa.Column('error_type', sa.String(120), nullable=True),
        sa.Column('message',    sa.Text(),      nullable=False),
        sa.Column('context',    sa.JSON(),      nullable=True,
                  comment='Datos adicionales en JSON: registro problemático, stack trace reducido, etc.'),
    )


def downgrade() -> None:
    op.drop_table('etl_job_errors')
    op.drop_table('etl_job_runs')
