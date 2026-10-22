from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import text
from app.database import SessionLocal
from app.domain.allocation import LowestFloorFirstStrategy, SpotAllocator
from app.domain.vehicle_type import VehicleType
from app.services.parking_service import ParkingService

service = ParkingService(SpotAllocator(LowestFloorFirstStrategy()))

def try_bus(i):
    with SessionLocal() as db:
        try:
            t = service.check_in(db, f"CONC-BUS-{i}", VehicleType.BUS)
            return t.spot_id
        except Exception:
            return None

def test_no_double_booking():
    with SessionLocal() as db:
        db.execute(text("TRUNCATE parking_sessions, vehicles RESTART IDENTITY CASCADE"))
        db.commit()
    with ThreadPoolExecutor(max_workers=10) as ex:
        results = list(ex.map(try_bus, range(10)))
    successes = [r for r in results if r is not None]
    assert len(successes) == 4  # 2 floors x 2 LARGE = 4
    assert len(set(successes)) == 4  # no duplicate spot