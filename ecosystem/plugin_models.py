"""Plugin system and marketplace models."""

from __future__ import annotations

from sqlalchemy import JSON, TIMESTAMP, Boolean, Column, Integer, String, Text, func

from shared.database import Base, BigInt


class Plugin(Base):
    """Available plugin in the marketplace catalog."""

    __tablename__ = "ecosystem_plugins"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    plugin_id = Column(
        String(200), unique=True, nullable=False
    )  # unique identifier e.g. "healthcare-analytics"
    name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    author = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(
        String(100), nullable=False
    )  # connector, dashboard_template, ai_agent, industry_solution, data_processor
    icon = Column(String(100), nullable=True)
    permissions = Column(JSON, nullable=True)  # list of required permissions
    dependencies = Column(JSON, nullable=True)  # list of plugin_id:version
    config_schema = Column(JSON, nullable=True)  # configuration fields
    is_verified = Column(Boolean, default=False, nullable=False)
    is_featured = Column(Boolean, default=False, nullable=False)
    install_count = Column(Integer, default=0, nullable=False)
    rating = Column(Integer, default=0, nullable=False)  # 0-5
    tags = Column(JSON, nullable=True)  # list of tags for search
    screenshots = Column(JSON, nullable=True)  # list of screenshot URLs
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class PluginInstallation(Base):
    """Plugin installation for an organization."""

    __tablename__ = "ecosystem_plugin_installations"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInt, nullable=False, index=True)
    plugin_id = Column(String(200), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    status = Column(
        String(20), nullable=False, default="installed"
    )  # installed, enabled, disabled, uninstalled
    configuration = Column(JSON, nullable=True)
    installed_by = Column(BigInt, nullable=True)
    installed_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class IndustryPackage(Base):
    """Industry solution package — pre-built templates for specific industries."""

    __tablename__ = "ecosystem_industry_packages"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    package_id = Column(String(200), unique=True, nullable=False)
    industry = Column(
        String(100), nullable=False
    )  # healthcare, education, banking, agriculture, retail, government
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=False)
    dataset_templates = Column(JSON, nullable=True)  # list of dataset schema templates
    dashboard_templates = Column(JSON, nullable=True)  # list of dashboard configs
    kpi_templates = Column(JSON, nullable=True)  # list of KPI definitions
    ai_insight_templates = Column(JSON, nullable=True)  # list of AI insight configs
    ml_model_templates = Column(JSON, nullable=True)  # list of ML model configs
    is_available = Column(Boolean, default=True, nullable=False)
    is_africa_optimized = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
