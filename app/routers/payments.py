from fastapi import APIRouter, Depends, HTTPException, status, Request
from datetime import datetime
from typing import List,Optional
import logging

from ..models.payment import PaymentInDB, PaymentStatus
from ..schemas.payment import PaymentOut, PaymentCreate
from ..utils.database import get_db
from ..utils.security import get_current_client
from ..utils.payment_processor import process_payment

payments_router = APIRouter()

@payments_router.post("/", response_model=PaymentOut)
async def create_payment(
    payment: PaymentCreate,
    request: Request,
    current_client: dict = Depends(get_current_client)
):
    db = request.app.mongodb
    
    
    booking = await db["bookings"].find_one({
        "_id": payment.booking_id,
        "client_id": current_client["_id"],
        "status": "accepted"
    })
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found or not eligible for payment"
        )
    
    # Process payment
    payment_result = await process_payment(
        payment.method,
        payment.amount,
        payment.token,
        request.app.settings
    )
    
    if not payment_result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=payment_result.message
        )
    
    
    payment_db = PaymentInDB(
        **payment.model_dump()(exclude={"token"}),
        client_id=current_client["_id"],
        artisan_id=booking["artisan_id"],
        status=PaymentStatus.COMPLETED if payment_result.success else PaymentStatus.FAILED,
        transaction_id=payment_result.transaction_id
    )
    
    inserted_payment = await db["payments"].insert_one(payment_db.dict(by_alias=True))
    created_payment = await db["payments"].find_one({"_id": inserted_payment.inserted_id})
    
    
    if payment_result.success:
        await db["bookings"].update_one(
            {"_id": payment.booking_id},
            {"$set": {"payment_status": "paid"}}
        )
    
    return PaymentOut(**created_payment)

@payments_router.get("/", response_model=List[PaymentOut])
async def get_client_payments(
    request: Request,
    status: Optional[str] = None,
    current_client: dict = Depends(get_current_client)
):
    db = request.app.mongodb
    
    query = {"client_id": current_client["_id"]}
    if status:
        query["status"] = status
    
    payments = await db["payments"].find(query).sort("created_at", -1).to_list(100)
    return [PaymentOut(**payment) for payment in payments]