from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.postgres.base import Base


class Source(Base):
    """Every piece of ingested data traces back to a Source row - the provenance anchor."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_type: Mapped[str] = mapped_column(String(50))  # website, pdf, gov_site, news, api...
    name: Mapped[str] = mapped_column(String(255))
    base_url: Mapped[str] = mapped_column(Text)
    crawl_frequency: Mapped[str] = mapped_column(String(20), default="weekly")
    last_crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    tos_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ConfidenceScore(Base):
    """One row per verified fact. entity_type/entity_id point at the fact being scored."""

    __tablename__ = "confidence_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(50))  # company, product, address, trade_claim
    entity_id: Mapped[int] = mapped_column(Integer)
    score: Mapped[float] = mapped_column(Float)  # 0.0 - 1.0
    verification_method: Mapped[str] = mapped_column(String(100))
    verifier_agent: Mapped[str] = mapped_column(String(100))
    corroborating_source_ids: Mapped[list[int]] = mapped_column(JSONB, default=list)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    name_ja: Mapped[str | None] = mapped_column(String(255))
    company_type: Mapped[str | None] = mapped_column(String(100))  # weaver, dyer, exporter...
    founded_year: Mapped[int | None] = mapped_column(Integer)
    website_url: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    moq: Mapped[str | None] = mapped_column(String(255))
    export_markets: Mapped[list[str]] = mapped_column(JSONB, default=list)
    certifications: Mapped[list[str]] = mapped_column(JSONB, default=list)
    social_media: Mapped[dict] = mapped_column(JSONB, default=dict)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"))
    confidence_score_id: Mapped[int | None] = mapped_column(ForeignKey("confidence_scores.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    products: Mapped[list["Product"]] = relationship(back_populates="company")
    contacts: Mapped[list["Contact"]] = relationship(back_populates="company")
    addresses: Mapped[list["Address"]] = relationship(back_populates="company")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str | None] = mapped_column(String(100))  # kimono fabric, obi, textile...
    fabric_type: Mapped[str | None] = mapped_column(String(100))  # silk, cotton, hemp, indigo...
    technique: Mapped[str | None] = mapped_column(String(100))  # kasuri, shibori, sashiko...
    certifications: Mapped[list[str]] = mapped_column(JSONB, default=list)
    price_range: Mapped[str | None] = mapped_column(String(100))
    production_capacity: Mapped[str | None] = mapped_column(String(255))
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"))
    confidence_score_id: Mapped[int | None] = mapped_column(ForeignKey("confidence_scores.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    company: Mapped["Company"] = relationship(back_populates="products")
    images: Mapped[list["Image"]] = relationship(back_populates="product")


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    contact_type: Mapped[str] = mapped_column(String(50))  # email, phone, owner, director
    value: Mapped[str] = mapped_column(String(255))
    role: Mapped[str | None] = mapped_column(String(100))
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"))

    company: Mapped["Company"] = relationship(back_populates="contacts")


class Address(Base):
    __tablename__ = "addresses"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))
    address_type: Mapped[str] = mapped_column(String(50), default="registered")  # registered, factory
    line1: Mapped[str | None] = mapped_column(String(255))
    line2: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    prefecture: Mapped[str | None] = mapped_column(String(100))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    country: Mapped[str | None] = mapped_column(String(100))
    lat: Mapped[float | None] = mapped_column(Float)
    lng: Mapped[float | None] = mapped_column(Float)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"))

    company: Mapped["Company"] = relationship(back_populates="addresses")


class TradeData(Base):
    """Country-level aggregate flows only (UN Comtrade). No company-level shipment data - see
    docs/data-sources.md for the Phase 2 plan to add company-level trade providers."""

    __tablename__ = "trade_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_country: Mapped[str] = mapped_column(String(100))
    partner_country: Mapped[str] = mapped_column(String(100))
    hs_code: Mapped[str] = mapped_column(String(20))
    trade_flow: Mapped[str] = mapped_column(String(20))  # import, export
    year: Mapped[int] = mapped_column(Integer)
    value_usd: Mapped[float | None] = mapped_column(Float)
    quantity: Mapped[float | None] = mapped_column(Float)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"))


class Association(Base):
    __tablename__ = "associations"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    name_ja: Mapped[str | None] = mapped_column(String(255))
    association_type: Mapped[str | None] = mapped_column(String(100))
    website_url: Mapped[str | None] = mapped_column(Text)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"))


class CompanyAssociation(Base):
    __tablename__ = "company_associations"

    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), primary_key=True)
    association_id: Mapped[int] = mapped_column(ForeignKey("associations.id"), primary_key=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"))


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    event_type: Mapped[str | None] = mapped_column(String(100))  # trade_fair, exhibition
    start_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    city: Mapped[str | None] = mapped_column(String(100))
    country: Mapped[str | None] = mapped_column(String(100))
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"))


class CompanyEvent(Base):
    __tablename__ = "company_events"

    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), primary_key=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"))


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    url: Mapped[str] = mapped_column(Text)
    document_type: Mapped[str] = mapped_column(String(50))  # html, pdf, catalog, brochure
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    raw_storage_path: Mapped[str | None] = mapped_column(Text)
    extracted_text_path: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(10))
    crawled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[str] = mapped_column(String(30), default="crawled")  # crawled, extracted, embedded, failed


class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"))
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"))
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    storage_path: Mapped[str] = mapped_column(Text)
    image_type: Mapped[str | None] = mapped_column(String(50))  # logo, factory, product
    ocr_status: Mapped[str] = mapped_column(String(30), default="not_processed")
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"))

    product: Mapped["Product | None"] = relationship(back_populates="images")


class EmbeddingMetadata(Base):
    """Bridges Postgres <-> Qdrant: one row per vector point stored."""

    __tablename__ = "embeddings_metadata"

    id: Mapped[int] = mapped_column(primary_key=True)
    qdrant_point_id: Mapped[str] = mapped_column(String(64), unique=True)
    qdrant_collection: Mapped[str] = mapped_column(String(100))
    source_table: Mapped[str] = mapped_column(String(50))
    source_row_id: Mapped[int] = mapped_column(Integer)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"))
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    chunk_text_hash: Mapped[str] = mapped_column(String(64))
    embedding_model: Mapped[str] = mapped_column(String(100))
    embedding_dim: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Swatch(Base):
    """One physical fabric swatch photo uploaded by a user. hex_color/rgb_* are machine-extracted
    (see app.pattern_rendering.color_extraction); label/notes are user-editable. This is
    user-generated design content, not a crawled/verified fact, so it deliberately has no
    source_id/confidence_score_id - created_at is the right provenance level here."""

    __tablename__ = "swatches"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(255))
    photo_storage_path: Mapped[str] = mapped_column(Text)
    hex_color: Mapped[str] = mapped_column(String(7))
    rgb_r: Mapped[int] = mapped_column(Integer)
    rgb_g: Mapped[int] = mapped_column(Integer)
    rgb_b: Mapped[int] = mapped_column(Integer)
    extraction_method: Mapped[str] = mapped_column(String(50), default="pillow_quantize")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    pattern_swatch_roles: Mapped[list["PatternSwatchRole"]] = relationship(back_populates="swatch")


class PatternMockup(Base):
    """One rendered pattern tile: a pattern_type + ordered swatches + render params. design_source
    is provenance/UI-filtering metadata only (manual vs. llm_suggested) - both render through the
    identical deterministic path in app.pattern_rendering, never a behavioral branch."""

    __tablename__ = "pattern_mockups"

    id: Mapped[int] = mapped_column(primary_key=True)
    pattern_type: Mapped[str] = mapped_column(String(50))
    render_params: Mapped[dict] = mapped_column(JSONB, default=dict)
    tile_storage_path: Mapped[str] = mapped_column(Text)
    tile_width_px: Mapped[int] = mapped_column(Integer)
    tile_height_px: Mapped[int] = mapped_column(Integer)
    design_source: Mapped[str] = mapped_column(String(20), default="manual")
    design_rationale: Mapped[str | None] = mapped_column(Text)
    batch_id: Mapped[str | None] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    swatch_roles: Mapped[list["PatternSwatchRole"]] = relationship(back_populates="mockup")
    concept_shots: Mapped[list["ConceptShot"]] = relationship(back_populates="mockup")


class PatternSwatchRole(Base):
    """Ordered join table: which swatch fills which role/position for a given mockup (e.g. gingham
    role_index 0="ground", 1="check"; tartan role_index 0..N = ordered sett sequence). A real FK
    join table (not a JSONB id array) so referential integrity holds if a swatch is edited/deleted,
    matching the CompanyAssociation/CompanyEvent precedent."""

    __tablename__ = "pattern_swatch_roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    mockup_id: Mapped[int] = mapped_column(ForeignKey("pattern_mockups.id"))
    swatch_id: Mapped[int] = mapped_column(ForeignKey("swatches.id"))
    role_index: Mapped[int] = mapped_column(Integer)

    mockup: Mapped["PatternMockup"] = relationship(back_populates="swatch_roles")
    swatch: Mapped["Swatch"] = relationship(back_populates="pattern_swatch_roles")


class ConceptShot(Base):
    """Opt-in, per-mockup AI photorealistic 'on a garment' image via a swappable image-gen
    provider (OpenAI gpt-image-1 by default - see app.imagegen.base.ImageGenProvider). Never
    created automatically - always a deliberate one-at-a-time action given per-image cost."""

    __tablename__ = "concept_shots"

    id: Mapped[int] = mapped_column(primary_key=True)
    mockup_id: Mapped[int] = mapped_column(ForeignKey("pattern_mockups.id"))
    provider_name: Mapped[str] = mapped_column(String(50))
    prompt_used: Mapped[str | None] = mapped_column(Text)
    garment_type: Mapped[str | None] = mapped_column(String(100))
    image_storage_path: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="completed")
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    mockup: Mapped["PatternMockup"] = relationship(back_populates="concept_shots")
