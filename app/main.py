from fastapi import Depends,FastAPI,HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from pathlib import Path
from fastapi.responses import FileResponse

from app.database import SessionLocal 
from app.domain.allocation import LowestFloorFirstStrategy,SpotAllocator

from app.domain.vehicle_type import VehicleType
from app.services.parking_service import(
    LotFullError,
    NoActiveSessionError,
    ParkingService,
    VehicleAlreadyParkedError
)


app = FastAPI(title="Smart Parking Lot")
service= ParkingService(SpotAllocator(LowestFloorFirstStrategy()))

def get_db():
    with SessionLocal() as db:
        yield db


class CheckInRequest(BaseModel):
    registration_number:str
    vehicle_type:VehicleType

class CheckOutRequest(BaseModel):
    registration_number : str


@app.post("/check-in", status_code=201)
def check_in(body:CheckInRequest,db:Session= Depends(get_db)):
    try:
        ticket=service.check_in(db,body.registration_number,body.vehicle_type)
    except VehicleAlreadyParkedError:
        raise HTTPException(status_code=409,detail="vehicle is alreadt parked")
    except LotFullError:
        raise HTTPException(status_code=409,detail="No free spot for this vehicle type")
    return{
        "ticket_id":ticket.id,
        "spot_id":ticket.spot_id,
        "entry_time":ticket.entry_time
    }

@app.post("/check-out")
def check_out(body:CheckOutRequest,db:Session=Depends(get_db)):

    try:
        ticket = service.check_out(db,body.registration_number)

    except NoActiveSessionError:
        raise HTTPException(status_code=404,detail="No active parking session")
    return{
        "ticket_id":ticket.id,
        "entry_time":ticket.entry_time,
        "entry_time":ticket.exit_time,
        "fee":str(ticket.fee_amount)
    }

@app.get("/availibility")
def availibilty (db:Session= Depends(get_db)):
    return service.avaliability(db)


@app.get("/status")
def status(db: Session = Depends(get_db)):
    return service.status(db)

STATIC_DIR =Path(__file__).parent /"static"


@app.get("/", include_in_schema=False)
def dashboard():
    return FileResponse(STATIC_DIR / "dashboard.html")


