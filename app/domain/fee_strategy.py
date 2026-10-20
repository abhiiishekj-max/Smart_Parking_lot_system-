import math
from datetime import timedelta

GRACE_PERIOD = timedelta(minutes=5)
ONE_HOUR = timedelta(hours =1)

def billable_hours(stay:timedelta) -> int:
    chargeable_time = stay - GRACE_PERIOD
    if chargeable_time <= timedelta(0):
        return 0
    return math.ceil(chargeable_time/ONE_HOUR)