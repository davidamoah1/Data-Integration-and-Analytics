"""Platform domain models — templates, collaboration, and branding.

These models extend AEDIP with product-level features:
  - Template marketplace (dashboard, KPI, ETL, report, AI prompt, industry packs)
  - Collaboration (comments, mentions, shared resources, activity timeline)
  - Organization branding (logo, theme, colors, email/report branding)
"""

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    BigInteger,
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)

from shared.database import Base, BigInt


# --- Template Marketplace ----------------------------------------------------


class Template(Base):
    """Reusable template for dashboards, KPIs, ETL pipelines, reports, etc."""

    __tablename__ = "platform_templates"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    template_type = Column(String(50), nullable=False, index=True)
    industry = Column(String(50), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    author = Column(String(255), nullable=True)
    version = Column(String(20), nullable=False, default="1.0.0")
    content = Column(JSON, nullable=False)
    tags = Column(JSON, nullable=True, default=list)
    is_public = Column(Boolean, nullable=False, default=True)
    is_featured = Column(Boolean, nullable=False, default=False)
    install_count = Column(Integer, nullable=False, default=0)
    rating_sum = Column(Integer, nullable=False, default=0)
    rating_count = Column(Integer, nullable=False, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class TemplateInstall(Base):
    """Tracks which organizations have installed which templates."""

    __tablename__ = "platform_template_installs"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    template_id = Column(BigInteger, ForeignKey("platform_templates.id"), nullable=False, index=True)
    organization_id = Column(BigInteger, nullable=True, index=True)
    installed_by = Column(BigInteger, nullable=False)
    installed_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


# --- Collaboration -----------------------------------------------------------


class Comment(Base):
    """Comment on a dashboard, report, pipeline, or other resource."""

    __tablename__ = "platform_comments"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(BigInteger, nullable=False, index=True)
    author_id = Column(BigInteger, nullable=False, index=True)
    parent_id = Column(BigInteger, ForeignKey("platform_comments.id"), nullable=True)
    body = Column(Text, nullable=False)
    mentions = Column(JSON, nullable=True, default=list)
    is_resolved = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class SharedResource(Base):
    """A resource shared with a user, team, or organization."""

    __tablename__ = "platform_shared_resources"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(BigInteger, nullable=False, index=True)
    shared_by = Column(BigInteger, nullable=False)
    shared_with_type = Column(String(20), nullable=False, default="user")
    shared_with_id = Column(BigInteger, nullable=False)
    permission = Column(String(20), nullable=False, default="view")
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class ActivityEvent(Base):
    """Activity timeline event for audit and collaboration."""

    __tablename__ = "platform_activity_events"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=True, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(BigInteger, nullable=True)
    event_metadata = Column("metadata", JSON, nullable=True, default=dict)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


# --- Branding ----------------------------------------------------------------


class OrganizationBranding(Base):
    """Organization-specific branding configuration."""

    __tablename__ = "platform_org_branding"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False, unique=True, index=True)
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(20), nullable=True, default="#6366f1")
    secondary_color = Column(String(20), nullable=True, default="#a78bfa")
    accent_color = Column(String(20), nullable=True, default="#22d3ee")
    theme_mode = Column(String(20), nullable=False, default="dark")
    company_name = Column(String(255), nullable=True)
    company_tagline = Column(String(500), nullable=True)
    email_footer = Column(Text, nullable=True)
    report_header_text = Column(String(255), nullable=True)
    report_footer_text = Column(String(255), nullable=True)
    custom_css = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
