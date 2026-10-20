import math
from datetime import timedelta , datetime
from abc import ABC,abstractmethod
from decimal import Decimal
from app.domain.vehicle_type import VehicleType

GRACE_PERIOD = timedelta(minutes=5)
ONE_HOUR = timedelta(hours =1)

def billable_hours(stay:timedelta) -> int:
    chargeable_time = stay - GRACE_PERIOD
    if chargeable_time <= timedelta(0):
        return 0
    return math.ceil(chargeable_time/ONE_HOUR)

class FeeStrategy(ABC):
    @abstractmethod
    def calculate(
            self,entry_time:datetime,exit_time:datetime,vehicle_type:VehicleType
    ) ->Decimal :
        """ Return the parking fee for one visit"""
class HourlyFeeStrategy(FeeStrategy):
    def __init__(self,hourly_rates: dict[VehicleType,Decimal]):
        self._hourly_rates= hourly_rates


    def calculate(self, entry_time:datetime,exit_time:datetime , vehicle_type:VehicleType)->Decimal:
        if exit_time < entry_time:
            raise ValueError("exit_time cannot be before entry time")
        if vehicle_type not in self. _hourly_rates:
            raise ValueError(f"No rate configured for {vehicle_type.value}")
        hours = billable_hours(exit_time - entry_time)
        return self._hourly_rates[vehicle_type] * hours 

    