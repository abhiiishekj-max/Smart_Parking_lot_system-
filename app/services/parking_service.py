from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.allocation import SpotAllocator
from app.domain.fee_strategy import HourlyFeeStrategy
from app.domain.spot_model import ParkingSpot
from app.domain.vehicle_type import VehicleType
from app.models.tables import RateRecord, SessionRecord, SpotRecord, VehicleRecord


class LotFullError(Exception):
    pass


class VehicleAlreadyParkedError(Exception):
    pass


class NoActiveSessionError(Exception):
    pass


class ParkingService:
    def __init__(self, allocator: SpotAllocator):
        self._allocator = allocator

    def check_in(
        self, db: Session, registration_number: str, vehicle_type: VehicleType
    ) -> SessionRecord:
        vehicle = self._get_or_create_vehicle(db, registration_number, vehicle_type)
        if self._open_session_for(db, vehicle.id) is not None:
            raise VehicleAlreadyParkedError(registration_number)

        spot = self._allocator.allocate(vehicle_type, self._free_spots(db))
        if spot is None:
            raise LotFullError(f"No free spot for {vehicle_type.value}")

        ticket = SessionRecord(
            vehicle_id=vehicle.id,
            spot_id=spot.id,
            entry_time=datetime.now(timezone.utc),
        )
        db.add(ticket)
        db.commit()
        return ticket

    def check_out(self, db: Session, registration_number: str) -> SessionRecord:
        vehicle = db.scalars(
            select(VehicleRecord).where(
                VehicleRecord.registration_number == registration_number
            )
        ).first()
        ticket = self._open_session_for(db, vehicle.id) if vehicle else None
        if ticket is None:
            raise NoActiveSessionError(registration_number)

        rates = {r.vehicle_type: r.hourly_rate for r in db.scalars(select(RateRecord))}
        exit_time = datetime.now(timezone.utc)
        ticket.fee_amount = HourlyFeeStrategy(rates).calculate(
            ticket.entry_time, exit_time, vehicle.vehicle_type
        )
        ticket.exit_time = exit_time
        db.commit()
        return ticket

    def _get_or_create_vehicle(self, db, registration_number, vehicle_type):
        vehicle = db.scalars(
            select(VehicleRecord).where(
                VehicleRecord.registration_number == registration_number
            )
        ).first()
        if vehicle is None:
            vehicle = VehicleRecord(
                registration_number=registration_number, vehicle_type=vehicle_type
            )
            db.add(vehicle)
            db.flush()
        return vehicle

    def _open_session_for(self, db, vehicle_id):
        return db.scalars(
            select(SessionRecord).where(
                SessionRecord.vehicle_id == vehicle_id,
                SessionRecord.exit_time.is_(None),
            )
        ).first()

    def _free_spots(self, db) -> list[ParkingSpot]:
        occupied = select(SessionRecord.spot_id).where(SessionRecord.exit_time.is_(None))
        rows = db.scalars(select(SpotRecord).where(SpotRecord.id.not_in(occupied)))
        return [
            ParkingSpot(id=r.id, floor=r.floor, number=r.number, spot_type=r.spot_type)
            for r in rows
        ]


    def avaliability (self,db:Session) -> dict[str,int]:
        counts : dict[str,int]={}
        for spot in self._free_spots(db):
            key = spot.spot_type.value
            counts[key] = counts.get(key,0) +1
        return counts
    