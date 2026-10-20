from datetime import timedelta

import pytest

from app.domain.fee_strategy import billable_hours

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