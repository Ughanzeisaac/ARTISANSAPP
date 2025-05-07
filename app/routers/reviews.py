from fastapi import APIRouter, Depends, HTTPException, status, Request
from datetime import datetime, timedelta
from typing import List
import logging

from ..models.review import ReviewInDB
from ..schemas.review import ReviewOut, ReviewCreate, ReviewUpdate
from ..utils.database import get_db
from ..utils.security import get_current_client
from ..models.client import PyObjectId

reviews_router = APIRouter()

@reviews_router.post("/", response_model=ReviewOut)
async def create_review(
    review: ReviewCreate,
    request: Request,
    current_client: dict = Depends(get_current_client)
):
    db = request.app.mongodb
    
    
    booking = await db["bookings"].find_one({
        "_id": review.booking_id,
        "client_id": current_client["_id"],
        "status": "completed"
    })
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found or not eligible for review"
        )
    
   
    existing_review = await db["reviews"].find_one({"booking_id": review.booking_id})
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review already exists for this booking"
        )
    
   
    review_db = ReviewInDB(
        **review.model_dump(),
        client_id=current_client["_id"],
        artisan_id=booking["artisan_id"]
    )
    
    inserted_review = await db["reviews"].insert_one(review_db.dict(by_alias=True))
    created_review = await db["reviews"].find_one({"_id": inserted_review.inserted_id})
    
    
    await update_artisan_rating(booking["artisan_id"], db)
    
    return ReviewOut(**created_review)

async def update_artisan_rating(artisan_id, db):
    pipeline = [
        {"$match": {"artisan_id": artisan_id}},
        {"$group": {
            "_id": None,
            "average_rating": {"$avg": "$rating"},
            "count": {"$sum": 1}
        }}
    ]
    
    result = await db["reviews"].aggregate(pipeline).to_list(1)
    if result:
        await db["artisans"].update_one(
            {"_id": artisan_id},
            {"$set": {
                "rating": result[0]["average_rating"],
                "review_count": result[0]["count"]
            }}
        )

@reviews_router.put("/{review_id}", response_model=ReviewOut)
async def update_review(
    review_id: str,
    review_update: ReviewUpdate,
    request: Request,
    current_client: dict = Depends(get_current_client)
):
    db = request.app.mongodb
    
    
    review = await db["reviews"].find_one({
        "_id": PyObjectId(review_id),
        "client_id": current_client["_id"]
    })
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
   
    review_age = datetime.now() - review["created_at"]
    if review_age.days > 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review can only be edited within 30 days of creation"
        )
    
   
    update_data = review_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.now()
    
    await db["reviews"].update_one(
        {"_id": PyObjectId(review_id)},
        {"$set": update_data}
    )
    
    updated_review = await db["reviews"].find_one({"_id": PyObjectId(review_id)})
    
    
    await update_artisan_rating(updated_review["artisan_id"], db)
    
    return ReviewOut(**updated_review)

@reviews_router.delete("/{review_id}")
async def delete_review(
    review_id: str,
    request: Request,
    current_client: dict = Depends(get_current_client)
):
    db = request.app.mongodb
    
   
    review = await db["reviews"].find_one({
        "_id": PyObjectId(review_id),
        "client_id": current_client["_id"]
    })
    
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
  
    await db["reviews"].delete_one({"_id": PyObjectId(review_id)})
    
   
    await update_artisan_rating(review["artisan_id"], db)
    
    return {"message": "Review deleted successfully"}