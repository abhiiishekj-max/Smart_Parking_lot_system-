from app.domain.allocation import LowestFloorFirstStrategy , SpotAllocator
from app.domain.spot_model import ParkingSpot , SpotType
from app.domain.vehicle_type import VehicleType

SPOTS = [
    ParkingSpot(id=1,floor=1,number=1,spot_type=SpotType.SMALL),
    ParkingSpot(id=2,floor=1,number=2,spot_type=SpotType.MEDIUM),
    ParkingSpot(id=3,floor=2,number=1,spot_type=SpotType.MEDIUM),
    ParkingSpot(id=4,floor=2,number=2,spot_type=SpotType.LARGE),
]

def make_allocator():
    return SpotAllocator(LowestFloorFirstStrategy())

def test_car_gets_medium_spot_on_lowest_floor():
    assert make_allocator().allocate(VehicleType.CAR,SPOTS).id ==2

def test_car_moves_to_next_floor_when_first_spot_is_taken():
    free = [s for s in SPOTS if s.id != 2]
    assert make_allocator().allocate(VehicleType.CAR, free).id == 3

def test_motorcycle_gets_small_spot():
    assert make_allocator().allocate(VehicleType.MOTORCYCLE , SPOTS).id == 1

def test_return_none_when_no_compatible_spot_is_free():
    free = [s for s in SPOTS if s.spot_type != SpotType.LARGE]
    assert make_allocator().allocate(VehicleType.BUS, free) is None
