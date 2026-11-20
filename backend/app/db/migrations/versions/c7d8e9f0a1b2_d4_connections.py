"""d4_connections

Revision ID: c7d8e9f0a1b2
Revises: b6c7d8e9f0a1
Create Date: 2026-11-20 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c7d8e9f0a1b2"
down_revision: Union[str, Sequence[str], None] = "b6c7d8e9f0a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "relationships",
        sa.Column(
            "directionality",
            sa.String(length=20),
            nullable=False,
            server_default="directed",
        ),
    )
    op.add_column(
        "relationships",
        sa.Column(
            "nature",
            sa.String(length=30),
            nullable=False,
            server_default="declarado",
        ),
    )
    op.add_column(
        "relationships",
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False,
            server_default="active",
        ),
    )
    op.add_column("relationships", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("relationships", sa.Column("justification", sa.Text(), nullable=True))
    op.add_column("relationships", sa.Column("source_locator", sa.Text(), nullable=True))
    op.add_column(
        "relationships", sa.Column("time_precision", sa.String(length=30), nullable=True)
    )
    op.add_column(
        "relationships", sa.Column("created_by", sa.String(length=100), nullable=True)
    )

    op.create_index("ix_relationships_status", "relationships", ["status"], unique=False)
    op.create_index("ix_relationships_nature", "relationships", ["nature"], unique=False)
    op.create_index(
        "ix_relationships_verification_status",
        "relationships",
        ["verification_status"],
        unique=False,
    )
    op.create_index(
        "ix_relationships_from_status",
        "relationships",
        ["from_entity_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_relationships_to_status",
        "relationships",
        ["to_entity_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_relationships_from_type",
        "relationships",
        ["from_entity_id", "relation_type"],
        unique=False,
    )
    op.create_index(
        "ix_relationships_to_type",
        "relationships",
        ["to_entity_id", "relation_type"],
        unique=False,
    )
    op.create_index(
        "ix_relationships_semantic_key",
        "relationships",
        ["from_entity_id", "to_entity_id", "relation_type", "directionality"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_relationships_semantic_key", table_name="relationships")
    op.drop_index("ix_relationships_to_type", table_name="relationships")
    op.drop_index("ix_relationships_from_type", table_name="relationships")
    op.drop_index("ix_relationships_to_status", table_name="relationships")
    op.drop_index("ix_relationships_from_status", table_name="relationships")
    op.drop_index("ix_relationships_verification_status", table_name="relationships")
    op.drop_index("ix_relationships_nature", table_name="relationships")
    op.drop_index("ix_relationships_status", table_name="relationships")

    op.drop_column("relationships", "created_by")
    op.drop_column("relationships", "time_precision")
    op.drop_column("relationships", "source_locator")
    op.drop_column("relationships", "justification")
    op.drop_column("relationships", "description")
    op.drop_column("relationships", "status")
    op.drop_column("relationships", "nature")
    op.drop_column("relationships", "directionality")
