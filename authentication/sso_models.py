"""SSO (Single Sign-On) domain models.

Future-ready architecture for OAuth2 / SAML enterprise identity providers.
Supports Google, Microsoft, and SAML-based SSO.
"""

from datetime import datetime, timezone

from sqlalchemy import JSON, TIMESTAMP, BigInteger, Boolean, Column, String, Text

from shared.database import Base, BigInt


class SSOConnection(Base):
    """SSO provider configuration for an organization.

    Each organization can configure multiple SSO providers.
    When a user authenticates via SSO, a linked SSOIdentity record is created.
    """

    __tablename__ = "sso_connections"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # google, microsoft, saml, okta, auth0
    client_id = Column(String(255), nullable=True)  # OAuth2 client_id
    client_secret_encrypted = Column(Text, nullable=True)  # Fernet-encrypted client_secret
    metadata_url = Column(Text, nullable=True)  # SAML metadata URL or IdP metadata
    scopes = Column(JSON, nullable=True)  # e.g. ["openid", "email", "profile"]
    field_mapping = Column(JSON, nullable=True)  # Map IdP fields to platform fields
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        TIMESTAMP,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
    )


class SSOIdentity(Base):
    """Links an external SSO identity to a platform user.

    A user may have multiple SSO identities (e.g. Google + Microsoft).
    """

    __tablename__ = "sso_identities"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # google, microsoft, saml
    external_id = Column(String(255), nullable=False)  # IdP's unique user ID
    external_email = Column(String(255), nullable=True)
    external_name = Column(String(255), nullable=True)
    metadata_ = Column("metadata", JSON, nullable=True, default=dict)
    created_at = Column(TIMESTAMP, default=datetime.now(timezone.utc), nullable=False)
    last_login_at = Column(TIMESTAMP, nullable=True)
