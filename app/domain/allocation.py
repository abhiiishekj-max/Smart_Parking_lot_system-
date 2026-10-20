from abc import ABC, abstractmethod
from app.domain.spot_model import ParkingSpot, SpotType
from app.domain.vehicle_type import VehicleType


COMPATIBLE_SPOT_TYPES= {
    VehicleType.MOTORCYCLE:[SpotType.SMALL],
    VehicleType.CAR:[SpotType.MEDIUM],
    VehicleType.BUS:[SpotType.LARGE],
}

class AllocationStrategy(ABC):
    @abstractmethod
    def choose(self, candidates: list[ParkingSpot]) -> ParkingSpot:
        """pick one spot form a non empty list of suitable free spot"""

class LowestFloorFirstStrategy(AllocationStrategy):
    def choose(self, candidates: list[ParkingSpot])-> ParkingSpot:
        return min(candidates , key=lambda spot:(spot.floor,spot.number))

class SpotAllocator:
    def __init__(self , strategy:AllocationStrategy):
        self._strategy = strategy


    def allocate(
            self,vehicle_type : VehicleType,free_spots:list[ParkingSpot])->ParkingSpot | None:
            allowed_type = COMPATIBLE_SPOT_TYPES[vehicle_type]
            candidates = [s for s in free_spots if s.spot_type in allowed_type]
            if not candidates:
                 return None
            return self._strategy.choose(candidates)
    