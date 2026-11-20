"""d2_claims_extend_and_links

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-11-19 22:10:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e3f4a5b6c7d8"
down_revision: Union[str, Sequence[str], None] = "d2e3f4a5b6c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("extracted_claims", recreate="always") as batch_op:
        batch_op.alter_column("source_id", existing_type=sa.String(length=36), nullable=True)
        batch_op.add_column(sa.Column("entity_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("research_source_id", sa.String(length=36), nullable=True))
        batch_op.add_column(
            sa.Column(
                "claim_origin",
                sa.String(length=50),
                nullable=False,
                server_default="manual",
            )
        )
        batch_op.add_column(sa.Column("justification", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("registered_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(
            sa.Column(
                "conflict_status",
                sa.String(length=50),
                nullable=False,
                server_default="none",
            )
        )
        batch_op.add_column(sa.Column("metadata_json", sa.JSON(), nullable=True))
        batch_op.create_foreign_key(
            "fk_extracted_claims_entity_id",
            "entities",
            ["entity_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "fk_extracted_claims_research_source_id",
            "research_sources",
            ["research_source_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_extracted_claims_entity_id", ["entity_id"], unique=False)
        batch_op.create_index(
            "ix_extracted_claims_research_source_id", ["research_source_id"], unique=False
        )
        batch_op.create_index(
            "ix_extracted_claims_conflict_status", ["conflict_status"], unique=False
        )
        batch_op.create_index(
            "ix_extracted_claims_entity_verification",
            ["entity_id", "verification_status"],
            unique=False,
        )
        batch_op.create_index(
            "ix_extracted_claims_entity_claim_type",
            ["entity_id", "claim_type"],
            unique=False,
        )

    op.create_table(
        "claim_entity_links",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("claim_id", sa.String(length=36), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("relevance", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["claim_id"], ["extracted_claims.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["entity_id"], ["entities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("claim_id", "entity_id", name="uq_claim_entity"),
    )
    op.create_index(
        "ix_claim_entity_links_claim_id", "claim_entity_links", ["claim_id"], unique=False
    )
    op.create_index(
        "ix_claim_entity_links_entity_id", "claim_entity_links", ["entity_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_claim_entity_links_entity_id", table_name="claim_entity_links")
    op.drop_index("ix_claim_entity_links_claim_id", table_name="claim_entity_links")
    op.drop_table("claim_entity_links")

    with op.batch_alter_table("extracted_claims", recreate="always") as batch_op:
        batch_op.drop_index("ix_extracted_claims_entity_claim_type")
        batch_op.drop_index("ix_extracted_claims_entity_verification")
        batch_op.drop_index("ix_extracted_claims_conflict_status")
        batch_op.drop_index("ix_extracted_claims_research_source_id")
        batch_op.drop_index("ix_extracted_claims_entity_id")
        batch_op.drop_constraint("fk_extracted_claims_research_source_id", type_="foreignkey")
        batch_op.drop_constraint("fk_extracted_claims_entity_id", type_="foreignkey")
        batch_op.drop_column("metadata_json")
        batch_op.drop_column("conflict_status")
        batch_op.drop_column("registered_at")
        batch_op.drop_column("justification")
        batch_op.drop_column("claim_origin")
        batch_op.drop_column("research_source_id")
        batch_op.drop_column("entity_id")
        batch_op.alter_column("source_id", existing_type=sa.String(length=36), nullable=False)
