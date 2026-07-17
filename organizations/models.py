"""SQLAlchemy ORM models for the Organization domain."""

from sqlalchemy import JSON, TIMESTAMP, BigInteger, Column, Integer, String, Text, func

from shared.database import Base, BigInt


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    website_url = Column(String(500), nullable=True)
    business_registration_number = Column(String(100), nullable=True)
    timezone = Column(String(64), nullable=False, default="UTC")
    date_format = Column(String(32), nullable=False, default="YYYY-MM-DD")
    locale = Column(String(16), nullable=False, default="en")
    branding = Column(JSON, nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Integer, nullable=False, default=0)
    deleted_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class Branch(Base):
    __tablename__ = "branches"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Integer, nullable=False, default=0)
    deleted_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class Department(Base):
    __tablename__ = "departments"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    organization_id = Column(BigInteger, nullable=False, index=True)
    branch_id = Column(BigInteger, nullable=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    head_user_id = Column(BigInteger, nullable=True)
    parent_id = Column(BigInteger, nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Integer, nullable=False, default=0)
    deleted_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class Team(Base):
    __tablename__ = "teams"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    department_id = Column(BigInteger, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    lead_user_id = Column(BigInteger, nullable=True)
    settings = Column(JSON, nullable=True)
    is_active = Column(Integer, nullable=False, default=1)
    is_deleted = Column(Integer, nullable=False, default=0)
    deleted_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(BigInt, primary_key=True, autoincrement=True)
    team_id = Column(BigInteger, nullable=False, index=True)
    user_id = Column(BigInteger, nullable=False, index=True)
    role = Column(String(32), nullable=False, default="member")
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
