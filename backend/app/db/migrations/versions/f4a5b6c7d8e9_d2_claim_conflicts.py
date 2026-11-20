"""d2_claim_conflicts

Revision ID: f4a5b6c7d8e9
Revises: e3f4a5b6c7d8
Create Date: 2026-11-19 22:15:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f4a5b6c7d8e9"
down_revision: Union[str, Sequence[str], None] = "e3f4a5b6c7d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "claim_conflicts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("claim_id", sa.String(length=36), nullable=False),
        sa.Column("conflicting_claim_id", sa.String(length=36), nullable=False),
        sa.Column("conflict_type", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="open"),
        sa.Column("detected_by", sa.String(length=50), nullable=False, server_default="user"),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("claim_id <> conflicting_claim_id", name="ck_claim_conflict_not_self"),
        sa.ForeignKeyConstraint(["claim_id"], ["extracted_claims.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["conflicting_claim_id"], ["extracted_claims.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("claim_id", "conflicting_claim_id", name="uq_claim_conflict_pair"),
    )
    op.create_index("ix_claim_conflicts_claim_id", "claim_conflicts", ["claim_id"], unique=False)
    op.create_index(
        "ix_claim_conflicts_conflicting_claim_id",
        "claim_conflicts",
        ["conflicting_claim_id"],
        unique=False,
    )
    op.create_index("ix_claim_conflicts_status", "claim_conflicts", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_claim_conflicts_status", table_name="claim_conflicts")
    op.drop_index("ix_claim_conflicts_conflicting_claim_id", table_name="claim_conflicts")
    op.drop_index("ix_claim_conflicts_claim_id", table_name="claim_conflicts")
    op.drop_table("claim_conflicts")
