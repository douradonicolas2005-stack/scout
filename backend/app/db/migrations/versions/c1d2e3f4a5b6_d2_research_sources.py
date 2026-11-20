"""d2_research_sources

Revision ID: c1d2e3f4a5b6
Revises: b7d1e2f3a4c5
Create Date: 2026-11-19 22:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, Sequence[str], None] = "b7d1e2f3a4c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "research_sources",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("source_type", sa.String(length=100), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("classification", sa.String(length=100), nullable=True),
        sa.Column("consulted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "reliability_status",
            sa.String(length=50),
            nullable=False,
            server_default="nao_avaliada",
        ),
        sa.Column("reliability_justification", sa.Text(), nullable=True),
        sa.Column(
            "verification_status",
            sa.String(length=50),
            nullable=False,
            server_default="nao_verificado",
        ),
        sa.Column("ingestion_source_id", sa.String(length=36), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_by", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["ingestion_source_id"], ["sources.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_research_sources_source_type", "research_sources", ["source_type"], unique=False
    )
    op.create_index(
        "ix_research_sources_reliability_status",
        "research_sources",
        ["reliability_status"],
        unique=False,
    )
    op.create_index(
        "ix_research_sources_verification_status",
        "research_sources",
        ["verification_status"],
        unique=False,
    )
    op.create_index(
        "ix_research_sources_domain", "research_sources", ["domain"], unique=False
    )
    op.create_index(
        "ix_research_sources_last_verified_at",
        "research_sources",
        ["last_verified_at"],
        unique=False,
    )
    op.create_index(
        "ix_research_sources_ingestion_source_id",
        "research_sources",
        ["ingestion_source_id"],
        unique=False,
    )
    op.create_index(
        "ix_research_sources_type_reliability",
        "research_sources",
        ["source_type", "reliability_status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_research_sources_type_reliability", table_name="research_sources")
    op.drop_index(
        "ix_research_sources_ingestion_source_id", table_name="research_sources"
    )
    op.drop_index(
        "ix_research_sources_last_verified_at", table_name="research_sources"
    )
    op.drop_index("ix_research_sources_domain", table_name="research_sources")
    op.drop_index(
        "ix_research_sources_verification_status", table_name="research_sources"
    )
    op.drop_index(
        "ix_research_sources_reliability_status", table_name="research_sources"
    )
    op.drop_index("ix_research_sources_source_type", table_name="research_sources")
    op.drop_table("research_sources")
