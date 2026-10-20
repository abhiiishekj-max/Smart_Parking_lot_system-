from datetime import timedelta , datetime
from decimal import Decimal

import pytest

from app.domain.fee_strategy import HourlyFeeStrategy, billable_hours
from app.domain.vehicle_type import VehicleType

@pytest.mark.parametrize(
    "stay , expected_hours",
    [
        (timedelta(minutes=3),0),
        (timedelta(minutes=5),0),
        (timedelta(minutes=5 ,seconds =1),1),
        (timedelta(hours=1 ,minutes= 5) ,1),
        (timedelta(hours =1, minutes = 5, seconds = 1),2),
        (timedelta(hours=2, minutes = 30 ),3),
        ],
)
def test_billable_hours(stay,expected_hours):
    assert billable_hours(stay) == expected_hours 


RATES = {
    VehicleType.MOTORCYCLE:Decimal("10"),
    VehicleType.CAR:Decimal("20"),
    VehicleType.BUS:Decimal("50"),
}

def test_car_staying_2h30_pays_three_hours():
    strategy = HourlyFeeStrategy(RATES)
    entry = datetime(2026,10,20,10,0)
    exit_ = entry + timedelta(hours=2,minutes=30)
    assert strategy.calculate(entry,exit_, VehicleType.CAR)==Decimal("60")

def test_motorcycle_pays_less_than_car_for_same_stay():
    strategy = HourlyFeeStrategy(RATES)
    entry = datetime(2026,10,20,10,0)
    exit_ = entry + timedelta(hours=2,minutes=30)
    bike_fee = strategy.calculate(entry,exit_,VehicleType.MOTORCYCLE)
    car_fee = strategy.calculate(entry,exit_,VehicleType.CAR)
    assert bike_fee<car_fee

def test_exit_before_entry_is_rejected():
    strategy = HourlyFeeStrategy(RATES)
    entry = datetime(2026,10,20,10,0)
    with pytest.raises(ValueError):
        strategy.calculate(entry,entry - timedelta(minutes=1), VehicleType.CAR)



