"""SQLAlchemy ORM models for Workspace and Invitation management.

Tables: workspaces, invitations
"""

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Column,
    Integer,
    String,
    func,
)

from shared.database import Base, BigInt


class Workspace(Base):
    """A workspace belonging to an organization or a personal user."""

    __tablename__ = "workspaces"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=True, index=True)
    user_id = Column(BigInteger, nullable=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(30), nullable=False, default="organization")
    is_active = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Integer, nullable=False, default=0)
    deleted_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class Invitation(Base):
    """An invitation for a user to join an organization."""

    __tablename__ = "invitations"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    role_id = Column(BigInteger, nullable=True)
    department_id = Column(BigInteger, nullable=True)
    token = Column(String(255), unique=True, nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    expires_at = Column(TIMESTAMP, nullable=False)
    accepted_at = Column(TIMESTAMP, nullable=True)
    accepted_by_user_id = Column(BigInteger, nullable=True)
    created_by = Column(BigInteger, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
