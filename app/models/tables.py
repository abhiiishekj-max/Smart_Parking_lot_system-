from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Numeric, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.domain.spot_model import SpotType
from app.domain.vehicle_type import VehicleType


def enum_column(enum_class):
    return Enum(
        enum_class,
        native_enum=False,
        values_callable=lambda members: [m.value for m in members],
    )


class SpotRecord(Base):
    __tablename__ = "parking_spots"
    __table_args__ = (UniqueConstraint("floor", "number"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    floor: Mapped[int]
    number: Mapped[int]
    spot_type: Mapped[SpotType] = mapped_column(enum_column(SpotType))


class RateRecord(Base):
    __tablename__ = "hourly_rates"

    vehicle_type: Mapped[VehicleType] = mapped_column(
        enum_column(VehicleType), primary_key=True
    )
    hourly_rate: Mapped[Decimal] = mapped_column(Numeric(10, 2))


class VehicleRecord(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(primary_key=True)
    registration_number: Mapped[str] = mapped_column(unique=True)
    vehicle_type: Mapped[VehicleType] = mapped_column(enum_column(VehicleType))


class SessionRecord(Base):
    __tablename__ = "parking_sessions"
    __table_args__ = (
        Index("uq_active_spot", "spot_id", unique=True, postgresql_where=text("exit_time IS NULL")),
        Index("uq_active_vehicle", "vehicle_id", unique=True, postgresql_where=text("exit_time IS NULL")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"))
    spot_id: Mapped[int] = mapped_column(ForeignKey("parking_spots.id"))
    entry_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    exit_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fee_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    