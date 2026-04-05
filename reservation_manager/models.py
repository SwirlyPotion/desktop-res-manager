"""Database models for properties, rental units, and reservations."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from reservation_manager.database import Base


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
