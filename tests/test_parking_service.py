from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.database import SessionLocal
from app.domain.allocation import LowestFloorFirstStrategy, SpotAllocator
from app.domain.vehicle_type import VehicleType
from app.services.parking_service import (
    LotFullError,
    NoActiveSessionError,
    ParkingService,
    VehicleAlreadyParkedError,
)


@pytest.fixture
def db():
    with SessionLocal() as session:
        session.execute(text("TRUNCATE parking_sessions, vehicles RESTART IDENTITY CASCADE"))
        session.commit()
        yield session


@pytest.fixture
def service():
    return ParkingService(SpotAllocator(LowestFloorFirstStrategy()))


def test_check_in_creates_open_ticket(db, service):
    ticket = service.check_in(db, "KA01AB1234", VehicleType.CAR)
    assert ticket.exit_time is None
    assert ticket.spot_id is not None


def test_same_vehicle_cannot_check_in_twice(db, service):
    service.check_in(db, "KA01AB1234", VehicleType.CAR)
    with pytest.raises(VehicleAlreadyParkedError):
        service.check_in(db, "KA01AB1234", VehicleType.CAR)


def test_two_cars_get_different_spots(db, service):
    first = service.check_in(db, "CAR-1", VehicleType.CAR)
    second = service.check_in(db, "CAR-2", VehicleType.CAR)
    assert first.spot_id != second.spot_id


def test_lot_full_for_buses(db, service):
    for i in range(4):
        service.check_in(db, f"BUS-{i}", VehicleType.BUS)
    with pytest.raises(LotFullError):
        service.check_in(db, "BUS-EXTRA", VehicleType.BUS)


def test_check_out_charges_fee_and_frees_spot(db, service):
    ticket = service.check_in(db, "KA01AB1234", VehicleType.CAR)
    spot_id = ticket.spot_id
    ticket.entry_time = ticket.entry_time - timedelta(hours=2, minutes=30)
    db.commit()

    done = service.check_out(db, "KA01AB1234")
    assert done.fee_amount == Decimal("60")
    assert done.exit_time is not None

    next_car = service.check_in(db, "OTHER", VehicleType.CAR)
    assert next_car.spot_id == spot_id


def test_check_out_without_check_in_fails(db, service):
    with pytest.raises(NoActiveSessionError):
        service.check_out(db, "UNKNOWN")

        