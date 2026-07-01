"""pattern mockups

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "swatches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("label", sa.String(255), nullable=False),
        sa.Column("photo_storage_path", sa.Text(), nullable=False),
        sa.Column("hex_color", sa.String(7), nullable=False),
        sa.Column("rgb_r", sa.Integer(), nullable=False),
        sa.Column("rgb_g", sa.Integer(), nullable=False),
        sa.Column("rgb_b", sa.Integer(), nullable=False),
        sa.Column("extraction_method", sa.String(50), server_default="pillow_quantize"),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "pattern_mockups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pattern_type", sa.String(50), nullable=False),
        sa.Column("render_params", postgresql.JSONB(), server_default="{}"),
        sa.Column("tile_storage_path", sa.Text(), nullable=False),
        sa.Column("tile_width_px", sa.Integer(), nullable=False),
        sa.Column("tile_height_px", sa.Integer(), nullable=False),
        sa.Column("design_source", sa.String(20), server_default="manual"),
        sa.Column("design_rationale", sa.Text()),
        sa.Column("batch_id", sa.String(64)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_pattern_mockups_batch_id", "pattern_mockups", ["batch_id"])

    op.create_table(
        "pattern_swatch_roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("mockup_id", sa.Integer(), sa.ForeignKey("pattern_mockups.id"), nullable=False),
        sa.Column("swatch_id", sa.Integer(), sa.ForeignKey("swatches.id"), nullable=False),
        sa.Column("role_index", sa.Integer(), nullable=False),
    )

    op.create_table(
        "concept_shots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("mockup_id", sa.Integer(), sa.ForeignKey("pattern_mockups.id"), nullable=False),
        sa.Column("provider_name", sa.String(50), nullable=False),
        sa.Column("prompt_used", sa.Text()),
        sa.Column("garment_type", sa.String(100)),
        sa.Column("image_storage_path", sa.Text()),
        sa.Column("status", sa.String(30), server_default="completed"),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("concept_shots")
    op.drop_table("pattern_swatch_roles")
    op.drop_index("ix_pattern_mockups_batch_id", table_name="pattern_mockups")
    op.drop_table("pattern_mockups")
    op.drop_table("swatches")
