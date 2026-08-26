"""add platform tables â€” templates, collaboration, branding

Revision ID: 0006_platform_tables
Revises: 0005_composite_indexes_analytics
Create Date: 2026-07-17
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_platform_tables"
down_revision: str | None = "0005_composite_indexes_analytics"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "platform_templates",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("template_type", sa.String(50), nullable=False),
        sa.Column("industry", sa.String(50), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("author", sa.String(255), nullable=True),
        sa.Column("version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("install_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rating_sum", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rating_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
    )
    with op.batch_alter_table("platform_templates", schema=None) as batch_op:
        batch_op.create_index("ix_platform_templates_template_type", ["template_type"])
        batch_op.create_index("ix_platform_templates_industry", ["industry"])

    op.create_table(
        "platform_template_installs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "template_id", sa.BigInteger(), sa.ForeignKey("platform_templates.id"), nullable=False
        ),
        sa.Column("organization_id", sa.BigInteger(), nullable=True),
        sa.Column("installed_by", sa.BigInteger(), nullable=False),
        sa.Column("installed_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
    )
    with op.batch_alter_table("platform_template_installs", schema=None) as batch_op:
        batch_op.create_index("ix_platform_template_installs_template_id", ["template_id"])
        batch_op.create_index("ix_platform_template_installs_organization_id", ["organization_id"])

    op.create_table(
        "platform_comments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.BigInteger(), nullable=False),
        sa.Column("author_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "parent_id", sa.BigInteger(), sa.ForeignKey("platform_comments.id"), nullable=True
        ),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("mentions", sa.JSON(), nullable=True),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
    )
    with op.batch_alter_table("platform_comments", schema=None) as batch_op:
        batch_op.create_index("ix_platform_comments_resource_type", ["resource_type"])
        batch_op.create_index("ix_platform_comments_resource_id", ["resource_id"])
        batch_op.create_index("ix_platform_comments_author_id", ["author_id"])
        batch_op.create_index("ix_platform_comments_parent_id", ["parent_id"])

    op.create_table(
        "platform_shared_resources",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("resource_type", sa.String(50), nullable=False),
        sa.Column("resource_id", sa.BigInteger(), nullable=False),
        sa.Column("shared_by", sa.BigInteger(), nullable=False),
        sa.Column("shared_with_type", sa.String(20), nullable=False, server_default="user"),
        sa.Column("shared_with_id", sa.BigInteger(), nullable=False),
        sa.Column("permission", sa.String(20), nullable=False, server_default="view"),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
    )
    with op.batch_alter_table("platform_shared_resources", schema=None) as batch_op:
        batch_op.create_index("ix_platform_shared_resources_resource_type", ["resource_type"])
        batch_op.create_index("ix_platform_shared_resources_resource_id", ["resource_id"])
        batch_op.create_index("ix_platform_shared_resources_shared_by", ["shared_by"])
        batch_op.create_index("ix_platform_shared_resources_shared_with_id", ["shared_with_id"])

    op.create_table(
        "platform_activity_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.BigInteger(), nullable=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", sa.BigInteger(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
    )
    with op.batch_alter_table("platform_activity_events", schema=None) as batch_op:
        batch_op.create_index("ix_platform_activity_events_organization_id", ["organization_id"])
        batch_op.create_index("ix_platform_activity_events_user_id", ["user_id"])
        batch_op.create_index("ix_platform_activity_events_event_type", ["event_type"])

    op.create_table(
        "platform_org_branding",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.BigInteger(), nullable=False, unique=True),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("primary_color", sa.String(20), nullable=True, server_default="#6366f1"),
        sa.Column("secondary_color", sa.String(20), nullable=True, server_default="#a78bfa"),
        sa.Column("accent_color", sa.String(20), nullable=True, server_default="#22d3ee"),
        sa.Column("theme_mode", sa.String(20), nullable=False, server_default="dark"),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("company_tagline", sa.String(500), nullable=True),
        sa.Column("email_footer", sa.Text(), nullable=True),
        sa.Column("report_header_text", sa.String(255), nullable=True),
        sa.Column("report_footer_text", sa.String(255), nullable=True),
        sa.Column("custom_css", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), server_default=sa.func.now(), nullable=False),
    )
    with op.batch_alter_table("platform_org_branding", schema=None) as batch_op:
        batch_op.create_index(
            "ix_platform_org_branding_organization_id", ["organization_id"], unique=True
        )


def downgrade() -> None:
    op.drop_table("platform_org_branding")
    op.drop_table("platform_activity_events")
    op.drop_table("platform_shared_resources")
    op.drop_table("platform_comments")
    op.drop_table("platform_template_installs")
    op.drop_table("platform_templates")
