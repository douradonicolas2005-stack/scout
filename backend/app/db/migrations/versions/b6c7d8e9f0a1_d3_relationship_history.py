"""d3_relationship_history

Revision ID: b6c7d8e9f0a1
Revises: a5b6c7d8e9f0
Create Date: 2026-11-19 23:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b6c7d8e9f0a1"
down_revision: Union[str, Sequence[str], None] = "a5b6c7d8e9f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "entity_interactions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("interaction_type", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("nature", sa.String(length=50), nullable=False),
        sa.Column(
            "status", sa.String(length=50), nullable=False, server_default="registered"
        ),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("time_precision", sa.String(length=30), nullable=True),
        sa.Column("channel", sa.String(length=100), nullable=True),
        sa.Column("location_text", sa.String(length=300), nullable=True),
        sa.Column("participants_text", sa.Text(), nullable=True),
        sa.Column("source_locator", sa.Text(), nullable=True),
        sa.Column("document_id", sa.String(length=36), nullable=True),
        sa.Column("research_source_id", sa.String(length=36), nullable=True),
        sa.Column("raw_record_id", sa.String(length=36), nullable=True),
        sa.Column("claim_id", sa.String(length=36), nullable=True),
        sa.Column("evidence_id", sa.String(length=36), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("justification", sa.Text(), nullable=True),
        sa.Column(
            "verification_status",
            sa.String(length=50),
            nullable=False,
            server_default="nao_verificado",
        ),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["entity_id"], ["entities.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["document_id"], ["documents.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["research_source_id"], ["research_sources.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["raw_record_id"], ["raw_records.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["claim_id"], ["extracted_claims.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["evidence_id"], ["evidence.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_entity_interactions_entity_id", "entity_interactions", ["entity_id"], unique=False
    )
    op.create_index(
        "ix_entity_interactions_interaction_type",
        "entity_interactions",
        ["interaction_type"],
        unique=False,
    )
    op.create_index(
        "ix_entity_interactions_nature", "entity_interactions", ["nature"], unique=False
    )
    op.create_index(
        "ix_entity_interactions_status", "entity_interactions", ["status"], unique=False
    )
    op.create_index(
        "ix_entity_interactions_occurred_at",
        "entity_interactions",
        ["occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_entity_interactions_entity_occurred",
        "entity_interactions",
        ["entity_id", "occurred_at"],
        unique=False,
    )
    op.create_index(
        "ix_entity_interactions_entity_nature",
        "entity_interactions",
        ["entity_id", "nature"],
        unique=False,
    )
    op.create_index(
        "ix_entity_interactions_entity_status",
        "entity_interactions",
        ["entity_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_entity_interactions_entity_status", table_name="entity_interactions")
    op.drop_index("ix_entity_interactions_entity_nature", table_name="entity_interactions")
    op.drop_index("ix_entity_interactions_entity_occurred", table_name="entity_interactions")
    op.drop_index("ix_entity_interactions_occurred_at", table_name="entity_interactions")
    op.drop_index("ix_entity_interactions_status", table_name="entity_interactions")
    op.drop_index("ix_entity_interactions_nature", table_name="entity_interactions")
    op.drop_index("ix_entity_interactions_interaction_type", table_name="entity_interactions")
    op.drop_index("ix_entity_interactions_entity_id", table_name="entity_interactions")
    op.drop_table("entity_interactions")
