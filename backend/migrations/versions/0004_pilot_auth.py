"""Sprint 4.5 pilot authentication and roles.

Revision ID: 0004_pilot_auth
Revises: 0003_waiting_list
"""
from alembic import op
import sqlalchemy as sa
revision="0004_pilot_auth"
down_revision="0003_waiting_list"
branch_labels=None
depends_on=None
def upgrade():
    role=sa.Enum("OWNER","SECRETARY","DOCTOR",name="userrole")
    op.create_table("users",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("clinic_id",sa.Integer(),sa.ForeignKey("clinics.id"),nullable=False),sa.Column("email",sa.String(255),nullable=False),sa.Column("full_name",sa.String(160),nullable=False),sa.Column("password_hash",sa.String(255),nullable=False),sa.Column("role",role,nullable=False,server_default="SECRETARY"),sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()),sa.Column("created_at",sa.DateTime(),nullable=False,server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_index("ix_users_clinic_id","users",["clinic_id"]); op.create_index("ix_users_email","users",["email"],unique=True); op.create_index("ix_users_role","users",["role"])
def downgrade():
    op.drop_table("users"); sa.Enum(name="userrole").drop(op.get_bind(),checkfirst=True)
