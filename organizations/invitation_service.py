"""Service for invitation and workspace management."""

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session as DbSession

from authentication.models import Role, User, UserRole
from authentication.repositories import RoleRepository, UserRepository, UserRoleRepository
from audit.models import AuditLog
from organizations.invitation_schemas import (
    InvitationAccept,
    InvitationCreate,
    SignupV2Request,
)
from organizations.models import Organization
from organizations.workspace_models import Invitation, Workspace
from shared.exceptions import AuthorizationError, ConflictError, NotFoundError, ValidationError
from shared.security import create_access_token, create_refresh_token, generate_token, hash_password


class InvitationService:
    def __init__(self, db: DbSession):
        self.db = db

    def create_invitation(
        self, org_id: int, request: InvitationCreate, created_by: int
    ) -> dict:
        role_repo = RoleRepository(self.db)
        role = role_repo.get_by_name(request.role_name)
        if not role:
            raise NotFoundError(f"Role '{request.role_name}' not found")

        if role.name in ("super_admin",):
            raise AuthorizationError("Cannot invite users as Super Admin")

        existing = self.db.execute(
            select(Invitation).where(
                Invitation.organization_id == org_id,
                Invitation.email == request.email,
                Invitation.status == "pending",
            )
        ).scalar_one_or_none()
        if existing:
            raise ConflictError("An active invitation already exists for this email")

        token = generate_token()
        invitation = Invitation(
            organization_id=org_id,
            email=request.email,
            role_id=role.id,
            department_id=request.department_id,
            token=token,
            status="pending",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            created_by=created_by,
        )
        self.db.add(invitation)
        self.db.flush()

        self._audit_log(
            user_id=created_by,
            org_id=org_id,
            action="invitation.sent",
            resource_type="invitation",
            resource_id=invitation.id,
            new_values={"email": request.email, "role": request.role_name},
        )

        self.db.commit()
        return self._invitation_to_dict(invitation, role.name)

    def accept_invitation(self, request: InvitationAccept) -> dict:
        invitation = self.db.execute(
            select(Invitation).where(Invitation.token == request.token)
        ).scalar_one_or_none()
        if not invitation:
            raise NotFoundError("Invalid invitation token")

        if invitation.status != "pending":
            raise ValidationError("Invitation is no longer valid")

        if invitation.expires_at < datetime.now(timezone.utc):
            self.db.execute(
                update(Invitation)
                .where(Invitation.id == invitation.id)
                .values(status="expired")
            )
            self.db.commit()
            raise ValidationError("Invitation has expired")

        user_repo = UserRepository(self.db)
        existing_user = user_repo.get_by_email(request.email)
        if existing_user:
            raise ConflictError("A user with this email already exists")

        role_repo = RoleRepository(self.db)
        role = self.db.get(Role, invitation.role_id) if invitation.role_id else None
        if not role:
            role = role_repo.get_by_name("viewer")

        user = User(
            email=invitation.email,
            password_hash=hash_password(request.password),
            full_name=request.full_name,
            organization_id=invitation.organization_id,
            department_id=invitation.department_id,
            email_verified_at=datetime.now(timezone.utc),
            is_active=1,
        )
        user_repo.create(user)
        self.db.flush()

        UserRoleRepository(self.db).set_user_roles(user.id, [role.id])

        self.db.execute(
            update(Invitation)
            .where(Invitation.id == invitation.id)
            .values(
                status="accepted",
                accepted_at=datetime.now(timezone.utc),
                accepted_by_user_id=user.id,
            )
        )

        self._audit_log(
            user_id=user.id,
            org_id=invitation.organization_id,
            action="invitation.accepted",
            resource_type="invitation",
            resource_id=invitation.id,
        )

        self._audit_log(
            user_id=user.id,
            org_id=invitation.organization_id,
            action="user.registered",
            resource_type="user",
            resource_id=user.id,
            new_values={"email": user.email, "role": role.name},
        )

        role_names = UserRoleRepository(self.db).get_roles_for_user(user.id)
        permission_names = UserRoleRepository(self.db).get_all_permissions_for_user(user.id)

        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={
                "email": user.email,
                "roles": role_names,
                "permissions": permission_names,
                "org_id": invitation.organization_id,
            },
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        from authentication.models import Session as UserSession

        session = UserSession(
            user_id=user.id,
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        self.db.add(session)

        self.db.commit()

        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "organization_id": invitation.organization_id,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 30 * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "roles": role_names,
                "permissions": permission_names,
                "organization_id": invitation.organization_id,
            },
        }

    def list_invitations(self, org_id: int) -> list[dict]:
        invitations = (
            self.db.execute(
                select(Invitation)
                .where(Invitation.organization_id == org_id)
                .order_by(Invitation.created_at.desc())
            )
            .scalars()
            .all()
        )
        result = []
        for inv in invitations:
            role = self.db.get(Role, inv.role_id) if inv.role_id else None
            result.append(self._invitation_to_dict(inv, role.name if role else None))
        return result

    def revoke_invitation(self, invitation_id: int, org_id: int) -> None:
        invitation = self.db.get(Invitation, invitation_id)
        if not invitation or invitation.organization_id != org_id:
            raise NotFoundError("Invitation not found")
        if invitation.status != "pending":
            raise ValidationError("Only pending invitations can be revoked")

        self.db.execute(
            update(Invitation)
            .where(Invitation.id == invitation_id)
            .values(status="revoked")
        )
        self.db.commit()

    def get_invitation_by_token(self, token: str) -> dict:
        invitation = self.db.execute(
            select(Invitation).where(Invitation.token == token)
        ).scalar_one_or_none()
        if not invitation:
            raise NotFoundError("Invalid invitation token")
        if invitation.status != "pending":
            raise ValidationError(f"Invitation is {invitation.status}")
        if invitation.expires_at < datetime.now(timezone.utc):
            raise ValidationError("Invitation has expired")

        org = self.db.get(Organization, invitation.organization_id)
        role = self.db.get(Role, invitation.role_id) if invitation.role_id else None
        return {
            "id": invitation.id,
            "email": invitation.email,
            "organization_name": org.name if org else "Unknown",
            "organization_id": invitation.organization_id,
            "role_name": role.name if role else "viewer",
            "expires_at": invitation.expires_at.isoformat() if invitation.expires_at else None,
        }

    def _invitation_to_dict(self, inv: Invitation, role_name: str | None) -> dict:
        return {
            "id": inv.id,
            "organization_id": inv.organization_id,
            "email": inv.email,
            "role_name": role_name,
            "department_id": inv.department_id,
            "status": inv.status,
            "expires_at": inv.expires_at,
            "accepted_at": inv.accepted_at,
            "created_by": inv.created_by,
            "created_at": inv.created_at,
        }

    def _audit_log(
        self,
        user_id: int | None,
        org_id: int | None,
        action: str,
        resource_type: str | None = None,
        resource_id: int | None = None,
        old_values: dict | None = None,
        new_values: dict | None = None,
    ):
        entry = AuditLog(
            user_id=user_id,
            organization_id=org_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
        )
        self.db.add(entry)


class RegistrationService:
    """Handles the three-mode registration flow."""

    def __init__(self, db: DbSession):
        self.db = db

    def register(self, request: SignupV2Request) -> dict:
        if request.registration_mode == "create_organization":
            return self._register_with_org(request)
        elif request.registration_mode == "join_organization":
            return self._register_via_invitation(request)
        elif request.registration_mode == "personal":
            return self._register_personal(request)
        else:
            raise ValidationError(
                f"Invalid registration_mode: {request.registration_mode}. "
                "Must be one of: create_organization, join_organization, personal"
            )

    def _register_with_org(self, request: SignupV2Request) -> dict:
        if not request.organization_name:
            raise ValidationError("Organization name is required for create_organization mode")

        user_repo = UserRepository(self.db)
        existing = user_repo.get_by_email(request.email)
        if existing:
            raise ConflictError("User with this email already exists")

        slug = request.organization_name.lower().strip().replace(" ", "-").replace("&", "and")
        existing_org = self.db.execute(
            select(Organization).where(Organization.slug == slug)
        ).scalar_one_or_none()
        if existing_org:
            raise ConflictError(
                "This organization already exists. Please request an invitation from your administrator."
            )

        org = Organization(
            name=request.organization_name,
            slug=slug,
            is_active=1,
        )
        self.db.add(org)
        self.db.flush()

        workspace = Workspace(
            organization_id=org.id,
            name=f"{request.organization_name} Workspace",
            type="organization",
        )
        self.db.add(workspace)
        self.db.flush()

        user = User(
            email=request.email,
            password_hash=hash_password(request.password),
            full_name=request.full_name,
            organization_id=org.id,
            email_verified_at=datetime.now(timezone.utc),
            is_active=1,
            onboarding_data={
                "country": request.country,
                "industry": request.industry,
                "organization_type": request.organization_type,
            },
        )
        user_repo.create(user)
        self.db.flush()

        role_repo = RoleRepository(self.db)
        org_admin_role = role_repo.get_by_name("org_admin")
        if not org_admin_role:
            org_admin_role = role_repo.get_by_name("viewer")
        if org_admin_role:
            UserRoleRepository(self.db).set_user_roles(user.id, [org_admin_role.id])

        self._audit_log(
            user_id=user.id,
            org_id=org.id,
            action="organization.created",
            resource_type="organization",
            resource_id=org.id,
            new_values={"name": org.name, "slug": org.slug},
        )

        self._audit_log(
            user_id=user.id,
            org_id=org.id,
            action="user.registered",
            resource_type="user",
            resource_id=user.id,
            new_values={"email": user.email, "mode": "create_organization"},
        )

        self._audit_log(
            user_id=user.id,
            org_id=org.id,
            action="role.assigned",
            resource_type="user",
            resource_id=user.id,
            new_values={"role": org_admin_role.name if org_admin_role else "viewer"},
        )

        role_names = UserRoleRepository(self.db).get_roles_for_user(user.id)
        permission_names = UserRoleRepository(self.db).get_all_permissions_for_user(user.id)

        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={
                "email": user.email,
                "roles": role_names,
                "permissions": permission_names,
                "org_id": org.id,
            },
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        from authentication.models import Session as UserSession

        session = UserSession(
            user_id=user.id,
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        self.db.add(session)

        self.db.commit()

        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "organization_id": org.id,
            "organization_name": org.name,
            "onboarding_completed": False,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 30 * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "roles": role_names,
                "permissions": permission_names,
                "organization_id": org.id,
                "organization_name": org.name,
            },
        }

    def _register_via_invitation(self, request: SignupV2Request) -> dict:
        if not request.invitation_token:
            raise ValidationError("Invitation token is required for join_organization mode")

        invitation = self.db.execute(
            select(Invitation).where(Invitation.token == request.invitation_token)
        ).scalar_one_or_none()
        if not invitation:
            raise NotFoundError("Invalid invitation token")

        if invitation.status != "pending":
            raise ValidationError(f"Invitation is {invitation.status}")

        if invitation.expires_at < datetime.now(timezone.utc):
            raise ValidationError("Invitation has expired")

        if invitation.email != request.email:
            raise ValidationError("Email does not match the invitation")

        user_repo = UserRepository(self.db)
        existing = user_repo.get_by_email(request.email)
        if existing:
            raise ConflictError("User with this email already exists")

        role_repo = RoleRepository(self.db)
        role = self.db.get(Role, invitation.role_id) if invitation.role_id else None
        if not role:
            role = role_repo.get_by_name("viewer")

        user = User(
            email=request.email,
            password_hash=hash_password(request.password),
            full_name=request.full_name,
            organization_id=invitation.organization_id,
            department_id=invitation.department_id,
            email_verified_at=datetime.now(timezone.utc),
            is_active=1,
        )
        user_repo.create(user)
        self.db.flush()

        UserRoleRepository(self.db).set_user_roles(user.id, [role.id])

        self.db.execute(
            update(Invitation)
            .where(Invitation.id == invitation.id)
            .values(
                status="accepted",
                accepted_at=datetime.now(timezone.utc),
                accepted_by_user_id=user.id,
            )
        )

        self._audit_log(
            user_id=user.id,
            org_id=invitation.organization_id,
            action="invitation.accepted",
            resource_type="invitation",
            resource_id=invitation.id,
        )

        self._audit_log(
            user_id=user.id,
            org_id=invitation.organization_id,
            action="user.registered",
            resource_type="user",
            resource_id=user.id,
            new_values={"email": user.email, "mode": "join_organization", "role": role.name},
        )

        role_names = UserRoleRepository(self.db).get_roles_for_user(user.id)
        permission_names = UserRoleRepository(self.db).get_all_permissions_for_user(user.id)

        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={
                "email": user.email,
                "roles": role_names,
                "permissions": permission_names,
                "org_id": invitation.organization_id,
            },
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        from authentication.models import Session as UserSession

        session = UserSession(
            user_id=user.id,
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        self.db.add(session)

        self.db.commit()

        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "organization_id": invitation.organization_id,
            "onboarding_completed": False,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 30 * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "roles": role_names,
                "permissions": permission_names,
                "organization_id": invitation.organization_id,
            },
        }

    def _register_personal(self, request: SignupV2Request) -> dict:
        user_repo = UserRepository(self.db)
        existing = user_repo.get_by_email(request.email)
        if existing:
            raise ConflictError("User with this email already exists")

        user = User(
            email=request.email,
            password_hash=hash_password(request.password),
            full_name=request.full_name,
            email_verified_at=datetime.now(timezone.utc),
            is_active=1,
            onboarding_data={
                "mode": "personal",
                "country": request.country,
                "industry": request.industry,
            },
        )
        user_repo.create(user)
        self.db.flush()

        workspace = Workspace(
            user_id=user.id,
            name=f"{request.full_name}'s Workspace",
            type="personal",
        )
        self.db.add(workspace)
        self.db.flush()

        role_repo = RoleRepository(self.db)
        viewer_role = role_repo.get_by_name("viewer")
        if viewer_role:
            UserRoleRepository(self.db).set_user_roles(user.id, [viewer_role.id])

        self._audit_log(
            user_id=user.id,
            org_id=None,
            action="user.registered",
            resource_type="user",
            resource_id=user.id,
            new_values={"email": user.email, "mode": "personal"},
        )

        role_names = UserRoleRepository(self.db).get_roles_for_user(user.id)
        permission_names = UserRoleRepository(self.db).get_all_permissions_for_user(user.id)

        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={
                "email": user.email,
                "roles": role_names,
                "permissions": permission_names,
                "org_id": None,
            },
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        from authentication.models import Session as UserSession

        session = UserSession(
            user_id=user.id,
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        self.db.add(session)

        self.db.commit()

        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "organization_id": None,
            "onboarding_completed": False,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 30 * 60,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "roles": role_names,
                "permissions": permission_names,
                "organization_id": None,
            },
        }

    def _audit_log(
        self,
        user_id: int | None,
        org_id: int | None,
        action: str,
        resource_type: str | None = None,
        resource_id: int | None = None,
        old_values: dict | None = None,
        new_values: dict | None = None,
    ):
        entry = AuditLog(
            user_id=user_id,
            organization_id=org_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
        )
        self.db.add(entry)
