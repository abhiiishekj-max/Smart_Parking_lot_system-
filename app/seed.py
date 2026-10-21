from decimal import Decimal
from sqlalchemy import select

from app.database import SessionLocal
from app.domain.spot_model import SpotType
from app.domain.vehicle_type import VehicleType
from app.models.tables import RateRecord,SpotRecord

FLOORS= [1,2]
SPOTS_PER_FLOOR =[
    (SpotType.SMALL,4),
    (SpotType.MEDIUM,6),
    (SpotType.LARGE,2),
]

RATES = {
    VehicleType.MOTORCYCLE:Decimal("10"),
    VehicleType.CAR :Decimal("20"),
    VehicleType.BUS:Decimal("50"),
}

# def seed():
#     with SessionLocal() as session:
#         if session.scalars(select(SpotRecord)).first() is not None:
#             print("already seeded")
#             return
#         for floor in FLOORS:
#             number = 1
#             for spot_type,count in SPOTS_PER_FLOOR:
#                 for _ in range(count):
#                     session.add(
#                         SpotRecord(floor = floor, number=number,spot_type = spot_type)
#                     )
#                     number+=1
#             for vehicle_type, rate in RATES.items():
#                 session.add(RateRecord(vehicle_type = vehicle_type, hourly_rate = rate))
#             session.commit()
#             print("seeded")

def seed():
    with SessionLocal() as session:
        if session.scalars(select(SpotRecord)).first() is None:
            for floor in FLOORS:
                number = 1
                for spot_type, count in SPOTS_PER_FLOOR:
                    for _ in range(count):
                        session.add(
                            SpotRecord(floor=floor, number=number, spot_type=spot_type)
                        )
                        number += 1
        if session.scalars(select(RateRecord)).first() is None:
            for vehicle_type, rate in RATES.items():
                session.add(RateRecord(vehicle_type=vehicle_type, hourly_rate=rate))
        session.commit()
        print("Seed complete")

if __name__ == "__main__":
    seed()
                                       
