"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("base_url", sa.Text(), nullable=False),
        sa.Column("crawl_frequency", sa.String(20), server_default="weekly"),
        sa.Column("last_crawled_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true()),
        sa.Column("tos_notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "confidence_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("verification_method", sa.String(100), nullable=False),
        sa.Column("verifier_agent", sa.String(100), nullable=False),
        sa.Column("corroborating_source_ids", postgresql.JSONB(), server_default="[]"),
        sa.Column("verified_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("name_ja", sa.String(255)),
        sa.Column("company_type", sa.String(100)),
        sa.Column("founded_year", sa.Integer()),
        sa.Column("website_url", sa.Text()),
        sa.Column("description", sa.Text()),
        sa.Column("moq", sa.String(255)),
        sa.Column("export_markets", postgresql.JSONB(), server_default="[]"),
        sa.Column("certifications", postgresql.JSONB(), server_default="[]"),
        sa.Column("social_media", postgresql.JSONB(), server_default="{}"),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id")),
        sa.Column("confidence_score_id", sa.Integer(), sa.ForeignKey("confidence_scores.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100)),
        sa.Column("fabric_type", sa.String(100)),
        sa.Column("technique", sa.String(100)),
        sa.Column("certifications", postgresql.JSONB(), server_default="[]"),
        sa.Column("price_range", sa.String(100)),
        sa.Column("production_capacity", sa.String(255)),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id")),
        sa.Column("confidence_score_id", sa.Integer(), sa.ForeignKey("confidence_scores.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("contact_type", sa.String(50), nullable=False),
        sa.Column("value", sa.String(255), nullable=False),
        sa.Column("role", sa.String(100)),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id")),
    )

    op.create_table(
        "addresses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), nullable=False),
        sa.Column("address_type", sa.String(50), server_default="registered"),
        sa.Column("line1", sa.String(255)),
        sa.Column("line2", sa.String(255)),
        sa.Column("city", sa.String(100)),
        sa.Column("prefecture", sa.String(100)),
        sa.Column("postal_code", sa.String(20)),
        sa.Column("country", sa.String(100)),
        sa.Column("lat", sa.Float()),
        sa.Column("lng", sa.Float()),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id")),
    )

    op.create_table(
        "trade_data",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reporter_country", sa.String(100), nullable=False),
        sa.Column("partner_country", sa.String(100), nullable=False),
        sa.Column("hs_code", sa.String(20), nullable=False),
        sa.Column("trade_flow", sa.String(20), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("value_usd", sa.Float()),
        sa.Column("quantity", sa.Float()),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id")),
    )

    op.create_table(
        "associations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("name_ja", sa.String(255)),
        sa.Column("association_type", sa.String(100)),
        sa.Column("website_url", sa.Text()),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id")),
    )

    op.create_table(
        "company_associations",
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), primary_key=True),
        sa.Column("association_id", sa.Integer(), sa.ForeignKey("associations.id"), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id")),
    )

    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(100)),
        sa.Column("start_date", sa.DateTime(timezone=True)),
        sa.Column("end_date", sa.DateTime(timezone=True)),
        sa.Column("city", sa.String(100)),
        sa.Column("country", sa.String(100)),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id")),
    )

    op.create_table(
        "company_events",
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id"), primary_key=True),
        sa.Column("event_id", sa.Integer(), sa.ForeignKey("events.id"), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id")),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("raw_storage_path", sa.Text()),
        sa.Column("extracted_text_path", sa.Text()),
        sa.Column("language", sa.String(10)),
        sa.Column("crawled_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("status", sa.String(30), server_default="crawled"),
    )
    op.create_index("ix_documents_content_hash", "documents", ["content_hash"])

    op.create_table(
        "images",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id")),
        sa.Column("company_id", sa.Integer(), sa.ForeignKey("companies.id")),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id")),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("image_type", sa.String(50)),
        sa.Column("ocr_status", sa.String(30), server_default="not_processed"),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id")),
    )

    op.create_table(
        "embeddings_metadata",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("qdrant_point_id", sa.String(64), nullable=False, unique=True),
        sa.Column("qdrant_collection", sa.String(100), nullable=False),
        sa.Column("source_table", sa.String(50), nullable=False),
        sa.Column("source_row_id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id")),
        sa.Column("chunk_index", sa.Integer(), server_default="0"),
        sa.Column("chunk_text_hash", sa.String(64), nullable=False),
        sa.Column("embedding_model", sa.String(100), nullable=False),
        sa.Column("embedding_dim", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("embeddings_metadata")
    op.drop_table("images")
    op.drop_index("ix_documents_content_hash", table_name="documents")
    op.drop_table("documents")
    op.drop_table("company_events")
    op.drop_table("events")
    op.drop_table("company_associations")
    op.drop_table("associations")
    op.drop_table("trade_data")
    op.drop_table("addresses")
    op.drop_table("contacts")
    op.drop_table("products")
    op.drop_table("companies")
    op.drop_table("confidence_scores")
    op.drop_table("sources")
