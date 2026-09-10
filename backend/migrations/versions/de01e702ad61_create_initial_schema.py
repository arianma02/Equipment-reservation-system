"""create initial schema

Revision ID: de01e702ad61
Revises:
Create Date: 2026-09-10 14:16:42.057073

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "de01e702ad61"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="user"),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
    )
    op.create_check_constraint("check_users_role", "users", "role IN ('user', 'admin')")
    op.create_check_constraint(
        "check_users_status", "users", "status IN ('active', 'disabled')"
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False, unique=True),
    )

    op.create_table(
        "equipment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("asset_tag", sa.String(), nullable=False, unique=True),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"]),
    )

    op.create_check_constraint(
        "check_equipment_status",
        "equipment",
        "status IN ('active', 'maintenance', 'retired')",
    )

    op.create_table(
        "reservations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("equipment_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="active"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"]),
    )

    op.create_check_constraint(
        "check_reservations_status", "reservations", "status IN ('active', 'cancelled')"
    )

    op.create_check_constraint(
        "check_reservations_dates", "reservations", "end_date >= start_date"
    )


def downgrade() -> None:
    op.drop_table("reservations")
    op.drop_table("equipment")
    op.drop_table("categories")
    op.drop_table("users")
