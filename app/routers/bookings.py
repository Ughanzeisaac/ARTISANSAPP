from fastapi import APIRouter, Depends, HTTPException, status, Request
from datetime import datetime,timedelta
from typing import List, Optional



from ..models.booking import BookingInDB, BookingStatus
from ..schemas.booking import BookingOut, BookingCreate
from ..utils.database import get_db
from ..utils.security import get_current_client
from ..utils.email import send_booking_confirmation_email
from ..models.client import PyObjectId

bookings_router = APIRouter()

@bookings_router.post("/", response_model=BookingOut)
async def create_booking(
    booking: BookingCreate,
    request: Request,
    current_client: dict = Depends(get_current_client)
):
    db = request.app.mongodb
    
    
    artisan = await db["artisans"].find_one({"_id": booking.artisan_id})
    if not artisan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artisan not found"
        )
    
   
    is_available = await check_artisan_availability(
        booking.artisan_id,
        booking.date,
        booking.duration,
        db
    )
    if not is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Artisan is not available at the requested time"
        )
    
    
    booking_db = BookingInDB(
        **booking.dict(),
        client_id=current_client["_id"],
        status=BookingStatus.PENDING
    )
    
    inserted_booking = await db["bookings"].insert_one(booking_db.dict(by_alias=True))
    created_booking = await db["bookings"].find_one({"_id": inserted_booking.inserted_id})
    
    # Send confirmation email
    await send_booking_confirmation_email(
        current_client["email"],
        current_client["name"],
        {
            "service_name": booking.service_name,
            "artisan_name": artisan["name"],
            "date": booking.date,
            "status": "pending"
        },
        request.app.settings
    )
    
    return BookingOut(**created_booking)

async def check_artisan_availability(artisan_id, start_time, duration, db):
    end_time = start_time + timedelta(hours=duration)
    
    # Check if artisan has any overlapping bookings
    overlapping_bookings = await db["bookings"].count_documents({
        "artisan_id": artisan_id,
        "status": {"$in": ["pending", "accepted"]},
        "$or": [
            {"date": {"$lt": end_time}, "end_time": {"$gt": start_time}},
            {"date": {"$gte": start_time, "$lt": end_time}}
        ]
    })
    
    return overlapping_bookings == 0

@bookings_router.get("/", response_model=List[BookingOut])
async def get_client_bookings(
    request: Request,
    status: Optional[str] = None,
    current_client: dict = Depends(get_current_client)
):
    db = request.app.mongodb
    
    query = {"client_id": current_client["_id"]}
    if status:
        query["status"] = status
    
    bookings = await db["bookings"].find(query).sort("date", 1).to_list(100)
    return [BookingOut(**booking) for booking in bookings]

@bookings_router.get("/{booking_id}", response_model=BookingOut)
async def get_booking(
    booking_id: str,
    request: Request,
    current_client: dict = Depends(get_current_client)
):
    db = request.app.mongodb
    
    booking = await db["bookings"].find_one({
        "_id": PyObjectId(booking_id),
        "client_id": current_client["_id"]
    })
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    return BookingOut(**booking)

@bookings_router.put("/{booking_id}/cancel")
async def cancel_booking(
    booking_id: str,
    request: Request,
    current_client: dict = Depends(get_current_client)
):
    db = request.app.mongodb
    
    result = await db["bookings"].update_one(
        {
            "_id": PyObjectId(booking_id),
            "client_id": current_client["_id"],
            "status": {"$in": ["pending", "accepted"]}
        },
        {"$set": {"status": "cancelled"}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking could not be cancelled"
        )
    
    return {"message": "Booking cancelled successfully"}