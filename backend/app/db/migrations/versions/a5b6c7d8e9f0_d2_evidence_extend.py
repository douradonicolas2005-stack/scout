"""d2_evidence_extend

Revision ID: a5b6c7d8e9f0
Revises: f4a5b6c7d8e9
Create Date: 2026-11-19 22:20:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a5b6c7d8e9f0"
down_revision: Union[str, Sequence[str], None] = "f4a5b6c7d8e9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("evidence", recreate="always") as batch_op:
        batch_op.alter_column("source_id", existing_type=sa.String(length=36), nullable=True)
        batch_op.add_column(sa.Column("document_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("research_source_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("evidence_type", sa.String(length=100), nullable=True))
        batch_op.add_column(
            sa.Column(
                "relation_type",
                sa.String(length=50),
                nullable=False,
                server_default="supports",
            )
        )
        batch_op.add_column(sa.Column("location_json", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("excerpt", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            )
        )
        batch_op.create_foreign_key(
            "fk_evidence_document_id",
            "documents",
            ["document_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "fk_evidence_research_source_id",
            "research_sources",
            ["research_source_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_evidence_document_id", ["document_id"], unique=False)
        batch_op.create_index(
            "ix_evidence_research_source_id", ["research_source_id"], unique=False
        )
        batch_op.create_index("ix_evidence_evidence_type", ["evidence_type"], unique=False)
        batch_op.create_index("ix_evidence_relation_type", ["relation_type"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("evidence", recreate="always") as batch_op:
        batch_op.drop_index("ix_evidence_relation_type")
        batch_op.drop_index("ix_evidence_evidence_type")
        batch_op.drop_index("ix_evidence_research_source_id")
        batch_op.drop_index("ix_evidence_document_id")
        batch_op.drop_constraint("fk_evidence_research_source_id", type_="foreignkey")
        batch_op.drop_constraint("fk_evidence_document_id", type_="foreignkey")
        batch_op.drop_column("updated_at")
        batch_op.drop_column("excerpt")
        batch_op.drop_column("location_json")
        batch_op.drop_column("relation_type")
        batch_op.drop_column("evidence_type")
        batch_op.drop_column("research_source_id")
        batch_op.drop_column("document_id")
        batch_op.alter_column("source_id", existing_type=sa.String(length=36), nullable=False)
