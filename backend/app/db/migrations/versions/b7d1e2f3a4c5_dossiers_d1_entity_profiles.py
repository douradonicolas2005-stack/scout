"""dossiers_d1_entity_profiles

Revision ID: b7d1e2f3a4c5
Revises: 426757a848bb
Create Date: 2026-11-19 21:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "b7d1e2f3a4c5"
down_revision: Union[str, Sequence[str], None] = "426757a848bb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("entities") as batch_op:
        batch_op.add_column(sa.Column("description", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column("profile_status", sa.String(length=50), nullable=False, server_default="active")
        )
        batch_op.add_column(sa.Column("primary_location", sa.String(length=300), nullable=True))
        batch_op.add_column(sa.Column("profile_data", sa.JSON(), nullable=True))
        batch_op.create_index("ix_entities_profile_status", ["profile_status"], unique=False)

    op.create_table(
        "entity_identifiers",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("id_type", sa.String(length=100), nullable=False),
        sa.Column("value", sa.String(length=500), nullable=False),
        sa.Column("normalized_value", sa.String(length=500), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["entity_id"], ["entities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_entity_identifiers_entity_id", "entity_identifiers", ["entity_id"], unique=False)
    op.create_index("ix_entity_identifiers_id_type", "entity_identifiers", ["id_type"], unique=False)
    op.create_index(
        "ix_entity_identifiers_normalized_value",
        "entity_identifiers",
        ["normalized_value"],
        unique=False,
    )
    op.create_index(
        "ix_entity_identifiers_type_norm",
        "entity_identifiers",
        ["id_type", "normalized_value"],
        unique=False,
    )

    op.create_table(
        "entity_aliases",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("normalized_name", sa.String(length=500), nullable=False),
        sa.Column("alias_type", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["entity_id"], ["entities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_entity_aliases_entity_id", "entity_aliases", ["entity_id"], unique=False)
    op.create_index("ix_entity_aliases_normalized_name", "entity_aliases", ["normalized_name"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_entity_aliases_normalized_name", table_name="entity_aliases")
    op.drop_index("ix_entity_aliases_entity_id", table_name="entity_aliases")
    op.drop_table("entity_aliases")

    op.drop_index("ix_entity_identifiers_type_norm", table_name="entity_identifiers")
    op.drop_index("ix_entity_identifiers_normalized_value", table_name="entity_identifiers")
    op.drop_index("ix_entity_identifiers_id_type", table_name="entity_identifiers")
    op.drop_index("ix_entity_identifiers_entity_id", table_name="entity_identifiers")
    op.drop_table("entity_identifiers")

    with op.batch_alter_table("entities") as batch_op:
        batch_op.drop_index("ix_entities_profile_status")
        batch_op.drop_column("profile_data")
        batch_op.drop_column("primary_location")
        batch_op.drop_column("profile_status")
        batch_op.drop_column("description")
