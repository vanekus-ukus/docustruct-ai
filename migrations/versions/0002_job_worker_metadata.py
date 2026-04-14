"""add worker metadata to jobs"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_job_worker_metadata"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("worker_task_id", sa.String(length=255), nullable=True))
    op.create_index("ix_jobs_worker_task_id", "jobs", ["worker_task_id"])


def downgrade() -> None:
    op.drop_index("ix_jobs_worker_task_id", table_name="jobs")
    op.drop_column("jobs", "worker_task_id")
