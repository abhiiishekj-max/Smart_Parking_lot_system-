from datetime import datetime, timezone

from sqlalchemy import func , select
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

    def status(self, db: Session) -> dict:
        open_rows = db.execute(
            select(SessionRecord, VehicleRecord)
            .join(VehicleRecord, SessionRecord.vehicle_id == VehicleRecord.id)
            .where(SessionRecord.exit_time.is_(None))
        ).all()
        parked = {ticket.spot_id: (ticket, vehicle) for ticket, vehicle in open_rows}

        spots = []
        all_spots = select(SpotRecord).order_by(SpotRecord.floor, SpotRecord.number)
        for spot in db.scalars(all_spots):
            ticket, vehicle = parked.get(spot.id, (None, None))
            spots.append(
                {
                    "id": spot.id,
                    "floor": spot.floor,
                    "number": spot.number,
                    "spot_type": spot.spot_type.value,
                    "plate": vehicle.registration_number if vehicle else None,
                    "vehicle_type": vehicle.vehicle_type.value if vehicle else None,
                    "entry_time": ticket.entry_time if ticket else None,
                }
            )

        done_rows = db.execute(
            select(SessionRecord, VehicleRecord)
            .join(VehicleRecord, SessionRecord.vehicle_id == VehicleRecord.id)
            .where(SessionRecord.exit_time.is_not(None))
            .order_by(SessionRecord.exit_time.desc())
            .limit(10)
        ).all()
        history = [
            {
                "plate": vehicle.registration_number,
                "vehicle_type": vehicle.vehicle_type.value,
                "entry_time": ticket.entry_time,
                "exit_time": ticket.exit_time,
                "fee": str(ticket.fee_amount),
            }
            for ticket, vehicle in done_rows
        ]

        revenue = db.scalar(select(func.coalesce(func.sum(SessionRecord.fee_amount), 0)))
        return {
            "total_spots": len(spots),
            "occupied_spots": len(parked),
            "revenue": str(revenue),
            "spots": spots,
            "history": history,
        }