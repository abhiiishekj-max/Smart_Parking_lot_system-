from dataclasses import dataclass
from enum import Enum

class SpotType(str,Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"

@dataclass(frozen= True)
class ParkingSpot:
    id:int
    floor: int
    number : int
    spot_type: SpotType