"""Database models for properties, rental units, reservations, and users."""

from __future__ import annotations

import base64
import enum
import hashlib
import hmac
import os
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

PASSWORD_SCHEME = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 390000
PASSWORD_SALT_BYTES = 16


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    OWNER = "owner"
    MANAGER = "manager"
    PERSONNEL = "personnel"


class RegistrationRequestStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


USER_ROLE_ENUM = Enum(
    UserRole,
    name="user_role",
    native_enum=False,
    values_callable=lambda roles: [role.value for role in roles],
)
REGISTRATION_REQUEST_STATUS_ENUM = Enum(
    RegistrationRequestStatus,
    name="registration_request_status",
    native_enum=False,
    values_callable=lambda statuses: [status.value for status in statuses],
)


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password cannot be empty.")

    salt = os.urandom(PASSWORD_SALT_BYTES)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS
    )

    salt_b64 = base64.b64encode(salt).decode("ascii")
    digest_b64 = base64.b64encode(digest).decode("ascii")
    return (
        f"{PASSWORD_SCHEME}$"
        f"{PASSWORD_ITERATIONS}$"
        f"{salt_b64}$"
        f"{digest_b64}"
    )


def verify_password_hash(password: str, password_hash: str) -> bool:
    try:
        scheme, iterations_raw, salt_b64, expected_digest_b64 = (
            password_hash.split("$", 3)
        )
        if scheme != PASSWORD_SCHEME:
            return False

        iterations = int(iterations_raw)
        salt = base64.b64decode(salt_b64)
        expected_digest = base64.b64decode(expected_digest_b64)
    except (TypeError, ValueError):
        return False

    candidate_digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return hmac.compare_digest(candidate_digest, expected_digest)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(200), unique=True, index=True, nullable=False
    )
    role: Mapped[UserRole] = mapped_column(
        USER_ROLE_ENUM, nullable=False, default=UserRole.PERSONNEL
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(30), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(), default=datetime.utcnow
    )

    def set_password(self, password: str) -> None:
        self.password_hash = hash_password(password)

    def verify_password(self, password: str) -> bool:
        return verify_password_hash(password, self.password_hash)


class UserRegistrationRequest(Base):
    __tablename__ = "user_registration_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    email: Mapped[str] = mapped_column(
        String(200), unique=True, index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(30), nullable=False)
    requested_role: Mapped[UserRole] = mapped_column(
        USER_ROLE_ENUM, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[RegistrationRequestStatus] = mapped_column(
        REGISTRATION_REQUEST_STATUS_ENUM,
        nullable=False,
        default=RegistrationRequestStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(), default=datetime.utcnow
    )


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text())

    units: Mapped[list[RentalUnit]] = relationship(
        back_populates="property", cascade="all, delete-orphan"
    )


class RentalUnit(Base):
    __tablename__ = "rental_units"

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(
        ForeignKey("properties.id"), nullable=False
    )
    unit_code: Mapped[str] = mapped_column(String(50), nullable=False)
    capacity: Mapped[int] = mapped_column(nullable=False, default=1)
    nightly_rate: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    property: Mapped[Property] = relationship(back_populates="units")
    reservations: Mapped[list[Reservation]] = relationship(
        back_populates="unit", cascade="all, delete-orphan"
    )


class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True)
    unit_id: Mapped[int] = mapped_column(
        ForeignKey("rental_units.id"), nullable=False
    )
    guest_name: Mapped[str] = mapped_column(String(120), nullable=False)
    guest_email: Mapped[str | None] = mapped_column(String(200))
    check_in: Mapped[date] = mapped_column(Date(), nullable=False)
    check_out: Mapped[date] = mapped_column(Date(), nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(), default=datetime.utcnow
    )

    unit: Mapped[RentalUnit] = relationship(back_populates="reservations")
