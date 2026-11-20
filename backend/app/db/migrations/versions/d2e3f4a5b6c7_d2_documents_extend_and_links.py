"""d2_documents_extend_and_links

Revision ID: d2e3f4a5b6c7
Revises: c1d2e3f4a5b6
Create Date: 2026-11-19 22:05:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, Sequence[str], None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Recreate documents to allow nullable source_id and add D2 fields (SQLite-safe).
    with op.batch_alter_table("documents", recreate="always") as batch_op:
        batch_op.alter_column("source_id", existing_type=sa.String(length=36), nullable=True)
        batch_op.add_column(sa.Column("document_type", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("origin_type", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("source_locator", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("content_hash", sa.String(length=128), nullable=True))
        batch_op.add_column(
            sa.Column(
                "verification_status",
                sa.String(length=50),
                nullable=False,
                server_default="nao_verificado",
            )
        )
        batch_op.add_column(sa.Column("access_level", sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column("license_terms", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "is_reference_only",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.add_column(sa.Column("research_source_id", sa.String(length=36), nullable=True))
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            )
        )
        batch_op.add_column(
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            )
        )
        batch_op.create_foreign_key(
            "fk_documents_research_source_id",
            "research_sources",
            ["research_source_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_documents_document_type", ["document_type"], unique=False)
        batch_op.create_index("ix_documents_content_hash", ["content_hash"], unique=False)
        batch_op.create_index(
            "ix_documents_verification_status", ["verification_status"], unique=False
        )
        batch_op.create_index(
            "ix_documents_research_source_id", ["research_source_id"], unique=False
        )
        batch_op.create_index("ix_documents_published_at", ["published_at"], unique=False)
        batch_op.create_index("ix_documents_captured_at", ["captured_at"], unique=False)

    op.create_table(
        "document_entity_links",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["entity_id"], ["entities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id", "entity_id", "role", name="uq_document_entity_role"
        ),
    )
    op.create_index(
        "ix_document_entity_links_document_id",
        "document_entity_links",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        "ix_document_entity_links_entity_id",
        "document_entity_links",
        ["entity_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_document_entity_links_entity_id", table_name="document_entity_links")
    op.drop_index(
        "ix_document_entity_links_document_id", table_name="document_entity_links"
    )
    op.drop_table("document_entity_links")

    with op.batch_alter_table("documents", recreate="always") as batch_op:
        batch_op.drop_index("ix_documents_captured_at")
        batch_op.drop_index("ix_documents_published_at")
        batch_op.drop_index("ix_documents_research_source_id")
        batch_op.drop_index("ix_documents_verification_status")
        batch_op.drop_index("ix_documents_content_hash")
        batch_op.drop_index("ix_documents_document_type")
        batch_op.drop_constraint("fk_documents_research_source_id", type_="foreignkey")
        batch_op.drop_column("updated_at")
        batch_op.drop_column("created_at")
        batch_op.drop_column("research_source_id")
        batch_op.drop_column("is_reference_only")
        batch_op.drop_column("license_terms")
        batch_op.drop_column("access_level")
        batch_op.drop_column("verification_status")
        batch_op.drop_column("content_hash")
        batch_op.drop_column("captured_at")
        batch_op.drop_column("occurred_at")
        batch_op.drop_column("source_locator")
        batch_op.drop_column("origin_type")
        batch_op.drop_column("description")
        batch_op.drop_column("document_type")
        batch_op.alter_column("source_id", existing_type=sa.String(length=36), nullable=False)
