"""Sprint 4.5A first-run setup and role security.

Revision ID: 0005_role_security
Revises: 0004_pilot_auth
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_role_security"
down_revision = "0004_pilot_auth"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(sa.Column("doctor_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_users_doctor_id_doctors", "doctors", ["doctor_id"], ["id"])
        batch_op.create_index("ix_users_doctor_id", ["doctor_id"])


def downgrade():
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index("ix_users_doctor_id")
        batch_op.drop_constraint("fk_users_doctor_id_doctors", type_="foreignkey")
        batch_op.drop_column("doctor_id")
