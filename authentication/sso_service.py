"""SSO (Single Sign-On) service layer.

Future-ready architecture for OAuth2 and SAML-based SSO.
Provides provider configuration, initiation, and callback handling.

Currently provides the interface and data layer. Actual OAuth2/SAML
flows require provider-specific SDKs (authlib, python3-saml) which
can be added when SSO is enabled in production.
"""

import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession

from authentication.sso_models import SSOConnection, SSOIdentity
from shared.exceptions import NotFoundError, ValidationError
from shared.security import encrypt_secret


class SSOService:
    """Service for SSO operations."""

    def __init__(self, db: DbSession):
        self.db = db

    # --- Organization SSO Configuration ---

    def create_connection(
        self,
        org_id: int,
        provider: str,
        client_id: str = None,
        client_secret: str = None,
        metadata_url: str = None,
        scopes: list[str] = None,
        field_mapping: dict = None,
    ) -> dict:
        """Configure an SSO provider for an organization."""
        existing = self.db.execute(
            select(SSOConnection).where(
                SSOConnection.organization_id == org_id,
                SSOConnection.provider == provider,
            )
        ).scalar_one_or_none()

        if existing:
            raise ValidationError(
                f"SSO provider '{provider}' is already configured for this organization"
            )

        conn = SSOConnection(
            organization_id=org_id,
            provider=provider,
            client_id=client_id,
            client_secret_encrypted=encrypt_secret(client_secret) if client_secret else None,
            metadata_url=metadata_url,
            scopes=scopes or ["openid", "email", "profile"],
            field_mapping=field_mapping,
            is_active=True,
        )
        self.db.add(conn)
        self.db.commit()
        return self._connection_to_dict(conn)

    def list_connections(self, org_id: int) -> list[dict]:
        """List SSO connections for an organization."""
        conns = (
            self.db.execute(
                select(SSOConnection).where(
                    SSOConnection.organization_id == org_id,
                    SSOConnection.is_active == True,  # noqa: E712
                )
            )
            .scalars()
            .all()
        )
        return [self._connection_to_dict(c) for c in conns]

    def delete_connection(self, org_id: int, provider: str):
        """Remove an SSO provider configuration."""
        conn = self.db.execute(
            select(SSOConnection).where(
                SSOConnection.organization_id == org_id,
                SSOConnection.provider == provider,
            )
        ).scalar_one_or_none()
        if not conn:
            raise NotFoundError("SSO connection not found")
        self.db.delete(conn)
        self.db.commit()

    # --- SSO Login Flow ---

    def initiate(self, provider: str, redirect_url: str = None) -> dict:
        """Initiate an SSO login flow.

        Returns authorization URL for OAuth2 or SAML redirect info.
        Actual implementation requires provider SDK integration.
        """
        state = secrets.token_urlsafe(32)

        # SSO login flow is not yet available. The data layer (SSOConnection,
        # SSOIdentity) is ready, but actual OAuth2/SAML exchange requires a
        # provider SDK (e.g. authlib, python3-saml) which is not yet
        # integrated. When SSO_ENABLED=true and a provider SDK is installed:
        # - OAuth2: Build authorization URL with client_id, redirect_uri, scope, state
        # - SAML: Build AuthnRequest with entity_id, ACS URL

        return {
            "provider": provider,
            "state": state,
            "authorization_url": None,  # Populated when SDK is configured
            "redirect_url": redirect_url,
            "status": "not_available",
            "message": "SSO login is not yet available. Use email/password authentication.",
        }

    def handle_callback(
        self, provider: str, code: str = None, state: str = None, saml_response: str = None
    ) -> dict:
        """Handle SSO provider callback.

        Exchanges authorization code for tokens, fetches user info,
        and links to a platform user via SSOIdentity.

        Actual implementation requires provider SDK integration.
        """
        # SSO callback handling is not yet available.  The full flow
        # requires a provider SDK (authlib / python3-saml).  Steps when
        # implemented:
        # 1. Exchange code for access_token (OAuth2) or parse SAML response
        # 2. Fetch user profile from IdP
        # 3. Find or create SSOIdentity
        # 4. If user exists, issue JWT tokens
        # 5. If user doesn't exist, create account or return registration prompt

        raise ValidationError(
            "SSO callback handling is not yet available. "
            "Use email/password authentication or contact your administrator."
        )

    # --- SSO Identity Management ---

    def get_user_sso_identities(self, user_id: int) -> list[dict]:
        """Get SSO identities linked to a user."""
        identities = (
            self.db.execute(select(SSOIdentity).where(SSOIdentity.user_id == user_id))
            .scalars()
            .all()
        )
        return [
            {
                "id": i.id,
                "provider": i.provider,
                "external_email": i.external_email,
                "external_name": i.external_name,
                "last_login_at": i.last_login_at,
                "created_at": i.created_at,
            }
            for i in identities
        ]

    def unlink_identity(self, user_id: int, provider: str):
        """Unlink an SSO identity from a user."""
        identity = self.db.execute(
            select(SSOIdentity).where(
                SSOIdentity.user_id == user_id,
                SSOIdentity.provider == provider,
            )
        ).scalar_one_or_none()
        if not identity:
            raise NotFoundError("SSO identity not found")
        self.db.delete(identity)
        self.db.commit()

    def _connection_to_dict(self, conn: SSOConnection) -> dict:
        return {
            "id": conn.id,
            "provider": conn.provider,
            "client_id": conn.client_id,
            "has_secret": bool(conn.client_secret_encrypted),
            "metadata_url": conn.metadata_url,
            "scopes": conn.scopes,
            "field_mapping": conn.field_mapping,
            "is_active": conn.is_active,
            "created_at": conn.created_at,
        }
