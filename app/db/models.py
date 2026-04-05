"""Database models for properties, rental units, reservations, and users."""

from __future__ import annotations

import base64
import enum
import hashlib
import hmac
import os
from decimal import Decimal
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.db.database import Base

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

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    mnemonic_name: Mapped[str | None] = mapped_column(
        String(50), nullable=True, index=True
    )
    address_en: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address_el: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(
        Numeric(10, 7), nullable=True
    )
    longitude: Mapped[float | None] = mapped_column(
        Numeric(10, 7), nullable=True
    )
    google_maps_pin: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    bedrooms_count: Mapped[int] = mapped_column(Integer, nullable=False)
    bathrooms_count: Mapped[float] = mapped_column(
        Numeric(3, 1), nullable=False
    )
    guests_standard: Mapped[int] = mapped_column(Integer, nullable=False)
    guests_maximum: Mapped[int] = mapped_column(Integer, nullable=False)
    area_sqm: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    @validates("bathrooms_count")
    def _validate_bathrooms_count(
        self,
        key: str,
        value: Decimal | float | int,
    ) -> Decimal:
        decimal_value = Decimal(str(value))
        if decimal_value <= 0:
            raise ValueError("bathrooms_count must be greater than zero.")

        # Bathrooms are allowed only in 0.5 increments.
        if (decimal_value * 2) % 1 != 0:
            raise ValueError("bathrooms_count must be a multiple of 0.5.")
        return decimal_value

    @validates("bedrooms_count")
    def _validate_bedrooms_count(self, key: str, value: int) -> int:
        if value < 0:
            raise ValueError("bedrooms_count must be 0 or greater.")
        return value

    @validates("area_sqm")
    def _validate_area_sqm(
        self,
        key: str,
        value: Decimal | float | int,
    ) -> Decimal:
        decimal_value = Decimal(str(value))
        if decimal_value <= 0:
            raise ValueError("area_sqm must be greater than zero.")
        return decimal_value

    @validates("latitude")
    def _validate_latitude(
        self,
        key: str,
        value: Decimal | float | int | None,
    ) -> Decimal | None:
        if value is None:
            return None

        decimal_value = Decimal(str(value))
        if decimal_value < Decimal("-90") or decimal_value > Decimal("90"):
            raise ValueError("latitude must be between -90 and 90.")
        return decimal_value

    @validates("longitude")
    def _validate_longitude(
        self,
        key: str,
        value: Decimal | float | int | None,
    ) -> Decimal | None:
        if value is None:
            return None

        decimal_value = Decimal(str(value))
        if decimal_value < Decimal("-180") or decimal_value > Decimal("180"):
            raise ValueError("longitude must be between -180 and 180.")
        return decimal_value

    @validates("guests_standard")
    def _validate_guests_standard(self, key: str, value: int) -> int:
        if value < 0:
            raise ValueError("guests_standard must be 0 or greater.")

        if self.guests_maximum is not None and value > self.guests_maximum:
            raise ValueError(
                "guests_standard cannot exceed guests_maximum."
            )
        return value

    @validates("guests_maximum")
    def _validate_guests_maximum(self, key: str, value: int) -> int:
        if value < 0:
            raise ValueError("guests_maximum must be 0 or greater.")

        if self.guests_standard is not None and value < self.guests_standard:
            raise ValueError(
                "guests_maximum cannot be less than guests_standard."
            )
        return value

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
